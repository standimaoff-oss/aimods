#version 150

// r27: volumetric smoke. Each puff is a sphere: ray/sphere intersection, short raymarch through tileable 3D noise
// (Perlin-Worley base + Worley detail), Beer-Lambert extinction, analytic self-shadowing towards the sun, Henyey-
// Greenstein phase, optional emission (fireballs / fire-lit smoke). The segment is clipped by the scene depth (copy of
// the depth buffer) so puffs blend softly into the ground instead of being cut by a flat billboard.
// Output is premultiplied (blend ONE, ONE_MINUS_SRC_ALPHA). tools/render/volsmoke_ref.py is a numpy port of this file.

uniform sampler2D Sampler0;   // 3D noise atlas: 32 slices of 32x32 (+1 px wrap border), 8 x 4 -> 272 x 136
uniform sampler2D Sampler1;   // scene depth (copy)
uniform mat4 InvProjMat;
uniform vec2 DepthSize;
uniform vec3 SunDir;          // towards the sun / moon, world space
uniform vec3 SunCol;          // directional light (relative to the lightmap brightness)
uniform vec3 AmbCol;          // sky ambient (relative)
uniform vec4 VolParams;       // x max steps, y detail octave on/off, z time (s), w global density
uniform float FogStart;
uniform float FogEnd;
uniform vec4 FogColor;

in vec3 vPos;
flat in vec4 vSphere;
flat in vec4 vParams;
flat in vec4 vColor;
flat in vec3 vLight;
flat in float vSteps;

out vec4 fragColor;

const vec2 ATLAS = vec2(272.0, 136.0);

vec4 slice(vec2 xy, float z) {
    float col = mod(z, 8.0);
    float row = floor(z / 8.0);
    vec2 px = vec2(col, row) * 34.0 + 1.0 + xy * 32.0;
    return texture(Sampler0, px / ATLAS);
}

vec4 volNoise(vec3 p) {
    vec3 q = fract(p);
    float z = q.z * 32.0 - 0.5;
    float z0 = floor(z);
    float f = z - z0;
    return mix(slice(q.xy, mod(z0 + 32.0, 32.0)), slice(q.xy, mod(z0 + 1.0, 32.0)), f);
}

float ign(vec2 p) {
    return fract(52.9829189 * fract(dot(p, vec2(0.06711056, 0.00583715))));
}

vec3 fireRamp(float t) {
    return vec3(1.0, 0.30 + 0.55 * t, 0.05 + 0.45 * t * t);
}

void main() {
    vec3 C = vSphere.xyz;
    float R = vSphere.w;
    vec3 D = normalize(vPos);
    float b = dot(C, D);
    float h = b * b - (dot(C, C) - R * R);
    if (h <= 0.0) discard;
    h = sqrt(h);
    float t0 = max(b - h, 0.0);
    float t1 = b + h;

    vec2 suv = gl_FragCoord.xy / DepthSize;
    float dz = texture(Sampler1, suv).r;
    if (dz < 1.0) {
        vec4 vp = InvProjMat * vec4(suv * 2.0 - 1.0, dz * 2.0 - 1.0, 1.0);
        t1 = min(t1, length(vp.xyz / vp.w));
    }
    if (t1 <= t0 + 0.001) discard;

    float seed = vParams.x;
    float heat = vParams.y;
    float age = vParams.w;
    float opac = clamp(vColor.a, 0.0, 0.985);
    // extinction chosen so that the chord through the centre has optical depth -ln(1 - alpha) whatever the radius
    float K = -log(1.0 - opac) * vParams.z * VolParams.w / (R * 0.62);
    float steps = vSteps;
    float dt = (t1 - t0) / steps;
    float jit = ign(gl_FragCoord.xy);

    // per-puff noise frame: random offset, slow turbulent rotation, upward drift while ageing
    float ang = (seed - 0.5) * 6.2832 + age * (seed - 0.5) * 2.5;
    float ca = cos(ang);
    float sa = sin(ang);
    vec3 off = vec3(seed * 7.13, seed * 3.71 - age * 0.35, seed * 5.29);

    vec3 L = normalize(SunDir);
    float mu = dot(D, L);
    float g = 0.35;
    float hg = (1.0 - g * g) / pow(1.0 + g * g - 2.0 * g * mu, 1.5);
    float phase = mix(1.0, hg, 0.5);
    vec3 alb = vColor.rgb;

    vec3 acc = vec3(0.0);
    float T = 1.0;
    for (int i = 0; i < 12; i++) {
        if (float(i) >= steps) break;
        float t = t0 + (float(i) + jit) * dt;
        vec3 q = (D * t - C) / R;
        float r2 = dot(q, q);
        if (r2 >= 1.0) continue;
        vec3 pq = vec3(q.x * ca - q.z * sa, q.y, q.x * sa + q.z * ca);
        float shape = 1.0 - r2;
        float base = volNoise(pq * 0.42 + off).r;
        float d = shape * 1.35 - (1.0 - base) * 0.95;
        if (VolParams.y > 0.5) {
            float det = volNoise(pq * 1.1 + off * 1.7).g;
            d -= (1.0 - det) * 0.3 * (1.0 - shape * 0.7);
        }
        if (d <= 0.0) continue;
        d = min(d, 1.0);
        float sig = d * K;
        float a = 1.0 - exp(-sig * dt);
        // optical depth from the sample to the sphere surface towards the light (analytic chord)
        float qL = dot(q, L);
        float ex = -qL + sqrt(max(qL * qL - r2 + 1.0, 0.0));
        float tl = ex * R * K * (0.30 + 0.40 * d);
        float sunT = exp(-tl) + 0.25 * exp(-tl * 0.2);
        float up = 0.62 + 0.38 * q.y;
        vec3 col = alb * vLight * (SunCol * (sunT * phase) + AmbCol * up);
        if (heat > 0.0) {
            float temp = heat * clamp(d * 1.5, 0.0, 1.0) * (1.0 - 0.55 * sqrt(r2));
            col += fireRamp(temp) * (temp * 3.0);
        }
        acc += T * a * col;
        T *= 1.0 - a;
        if (T < 0.01) break;
    }
    float alpha = 1.0 - T;
    if (alpha < 0.004) discard;
    float fogT = clamp((t0 + 0.25 * (t1 - t0) - FogStart) / max(FogEnd - FogStart, 1.0), 0.0, 1.0);
    acc = mix(acc, FogColor.rgb * alpha, fogT * FogColor.a);
    fragColor = vec4(acc, alpha);
}
