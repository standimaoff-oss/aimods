#version 150

// r27: volumetric smoke puff (sphere impostor). The quad faces the puff centre; the fragment shader raymarches the
// sphere. Position/Sphere are camera-relative world coordinates (ModelViewMat = camera rotation only).

in vec3 Position;
in vec4 Color;
in ivec2 UV2;
in vec4 Sphere;   // xyz centre, w radius
in vec4 Params;   // x seed 0..1, y heat 0..1 (emission), z density multiplier, w age 0..1

uniform sampler2D Sampler2;   // lightmap
uniform mat4 ModelViewMat;
uniform mat4 ProjMat;
uniform vec2 DepthSize;
uniform vec4 VolParams;       // x max steps, y detail octave, z time (s), w global density

out vec3 vPos;
flat out vec4 vSphere;
flat out vec4 vParams;
flat out vec4 vColor;
flat out vec3 vLight;
flat out float vSteps;

void main() {
    gl_Position = ProjMat * ModelViewMat * vec4(Position, 1.0);
    vPos = Position;
    vSphere = Sphere;
    vParams = Params;
    vColor = Color;
    vLight = texelFetch(Sampler2, UV2 / 16, 0).rgb;
    // fewer raymarch steps for puffs that are small on screen
    float dist = max(length(Sphere.xyz), Sphere.w);
    float pix = Sphere.w / dist * ProjMat[1][1] * DepthSize.y * 0.5;
    vSteps = clamp(floor(pix / 12.0), 3.0, VolParams.x);
}
