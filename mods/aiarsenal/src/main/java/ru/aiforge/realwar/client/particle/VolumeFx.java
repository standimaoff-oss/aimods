package ru.aiforge.realwar.client.particle;

import com.google.common.collect.ImmutableMap;
import com.mojang.blaze3d.pipeline.RenderTarget;
import com.mojang.blaze3d.pipeline.TextureTarget;
import com.mojang.blaze3d.platform.GlStateManager;
import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.BufferBuilder;
import com.mojang.blaze3d.vertex.DefaultVertexFormat;
import com.mojang.blaze3d.vertex.Tesselator;
import com.mojang.blaze3d.vertex.VertexFormat;
import com.mojang.blaze3d.vertex.VertexFormatElement;
import java.lang.reflect.Method;
import net.minecraft.Util;
import net.minecraft.client.Camera;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.ParticleRenderType;
import net.minecraft.client.renderer.ShaderInstance;
import net.minecraft.client.renderer.texture.TextureManager;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.Level;
import net.minecraft.util.Mth;
import org.joml.Matrix4f;
import org.joml.Vector3f;
import org.lwjgl.opengl.GL30;
import ru.aiforge.realwar.RWConfig;
import ru.aiforge.realwar.RealWar;
import ru.aiforge.realwar.particle.VSmokeOptions;

/**
 * r27: volumetric smoke. Every non-additive {@link FxParticle} (explosion smoke, rocket trails, nuclear clouds, smoke
 * screens, burning wrecks ...) is drawn as a raymarched sphere impostor with the core shader {@code aiarsenal:volsmoke}
 * instead of a flat smoke sprite: 3D noise, self-shadowing from the sun, soft intersection with the ground (the segment
 * is clipped by a copy of the depth buffer), emission for fireballs. Falls back to the old sprites when the shader did
 * not load, when an Oculus/Iris shader pack is active, after a GL error, or when {@code volumetricSmoke=false}.
 */
public final class VolumeFx {
    public static final VertexFormatElement ELEMENT_SPHERE = new VertexFormatElement(3, VertexFormatElement.Type.FLOAT, VertexFormatElement.Usage.UV, 4);
    public static final VertexFormatElement ELEMENT_PARAMS = new VertexFormatElement(4, VertexFormatElement.Type.FLOAT, VertexFormatElement.Usage.UV, 4);
    /** Position, Color, UV2 (light), Sphere (camera-relative centre + radius), Params (seed, heat, density, age). */
    public static final VertexFormat FORMAT = new VertexFormat(ImmutableMap.<String, VertexFormatElement>builder()
            .put("Position", DefaultVertexFormat.ELEMENT_POSITION)
            .put("Color", DefaultVertexFormat.ELEMENT_COLOR)
            .put("UV2", DefaultVertexFormat.ELEMENT_UV2)
            .put("Sphere", ELEMENT_SPHERE)
            .put("Params", ELEMENT_PARAMS)
            .build());
    public static final ResourceLocation NOISE = new ResourceLocation("aiarsenal", "textures/fx/volnoise.png");
    /** puff radius relative to the sprite half-size (the smoke sprites fill ~85 % of their quad) */
    public static final float RADIUS_K = 0.85f;
    /** sprite alpha -> centre opacity of the volume (the sprites were already soft at their centre) */
    public static final float ALPHA_K = 0.92f;

    private static ShaderInstance shader;
    private static boolean failed;
    private static boolean on;
    private static TextureTarget depth;
    private static long frame;
    /** puffs containing the camera this frame: each one is a full-screen raymarch, so they are capped */
    private static int inside;
    private static final int MAX_INSIDE = 8;
    private static long copiedFrame = -1L;
    private static boolean irisChecked;
    private static Object irisApi;
    private static Method irisInUse;

    public static final ParticleRenderType TYPE = new ParticleRenderType() {
        @Override
        public void begin(BufferBuilder b, TextureManager tm) {
            VolumeFx.setup();
            b.begin(VertexFormat.Mode.QUADS, FORMAT);
        }

        @Override
        public void end(Tesselator t) {
            try {
                t.end();
            } finally {
                VolumeFx.teardown();
            }
        }

        @Override
        public String toString() {
            return "aiarsenal:volume";
        }
    };

    private VolumeFx() {
    }

    public static void setShader(ShaderInstance s) {
        shader = s;
        failed = false;
    }

    /** Called once per frame by {@link FxSystem#render} before anything is drawn. */
    static void beginFrame() {
        frame++;
        inside = 0;
        boolean want = false;
        try {
            want = shader != null && !failed && RWConfig.CLIENT.volumetricSmoke.get() && !shaderPackInUse();
        } catch (Throwable ignored) {
        }
        on = want;
    }

    /** true while volumetric smoke is used this frame (cached, cheap: called per particle). */
    public static boolean on() {
        return on;
    }

    static void fail(Throwable t) {
        if (!failed) {
            RealWar.LOGGER.error("r27: volumetric smoke disabled after a render error - flat smoke sprites are used", t);
        }
        failed = true;
        on = false;
    }

    private static boolean shaderPackInUse() {
        if (!irisChecked) {
            irisChecked = true;
            try {
                Class<?> c = Class.forName("net.irisshaders.iris.api.v0.IrisApi");
                irisApi = c.getMethod("getInstance").invoke(null);
                irisInUse = c.getMethod("isShaderPackInUse");
            } catch (Throwable t) {
                irisApi = null;
            }
        }
        if (irisApi == null) {
            return false;
        }
        try {
            return (Boolean) irisInUse.invoke(irisApi);
        } catch (Throwable t) {
            return false;
        }
    }

    // ------------------------------------------------------------------ GL state
    private static void setup() {
        Minecraft mc = Minecraft.getInstance();
        copyDepth(mc);
        ShaderInstance sh = shader;
        RenderSystem.setShader(() -> sh);
        RenderSystem.setShaderTexture(0, NOISE);
        RenderSystem.setShaderTexture(1, depth.getDepthTextureId());
        // Sampler2 = lightmap: bound by FxSystem (LightTexture.turnOnLightLayer)
        sh.safeGetUniform("InvProjMat").set(new Matrix4f(RenderSystem.getProjectionMatrix()).invert());
        sh.safeGetUniform("DepthSize").set((float) depth.width, (float) depth.height);
        lighting(mc, sh);
        int q = RWConfig.CLIENT.volumetricQuality.get();
        float steps = q <= 1 ? 6.0f : (q == 2 ? 10.0f : 16.0f);   // r28: 6/10/16 (was 5/8/12)
        sh.safeGetUniform("VolParams").set(steps, q >= 2 ? 1.0f : 0.0f, (float) (Util.getMillis() % 3600000L) / 1000.0f, 1.0f);
        RenderSystem.disableDepthTest();          // occlusion is done in the shader against the depth copy
        RenderSystem.depthMask(false);
        RenderSystem.disableCull();
        RenderSystem.enableBlend();
        RenderSystem.blendFunc(GlStateManager.SourceFactor.ONE, GlStateManager.DestFactor.ONE_MINUS_SRC_ALPHA);
        FxParticle.fogPush();
    }

    private static void teardown() {
        FxParticle.fogPop();
        RenderSystem.enableDepthTest();
        RenderSystem.depthMask(true);
        RenderSystem.enableCull();
        RenderSystem.defaultBlendFunc();
    }

    /** Copies the depth buffer of the main target once per frame (the volumes read it, nothing writes it meanwhile). */
    private static void copyDepth(Minecraft mc) {
        if (depth != null && copiedFrame == frame) {
            return;
        }
        RenderTarget main = mc.getMainRenderTarget();
        int prevDraw = GlStateManager._getInteger(GL30.GL_DRAW_FRAMEBUFFER_BINDING);
        int prevRead = GlStateManager._getInteger(GL30.GL_READ_FRAMEBUFFER_BINDING);
        if (depth == null) {
            depth = new TextureTarget(main.width, main.height, true, Minecraft.ON_OSX);
        }
        if (main.isStencilEnabled() && !depth.isStencilEnabled()) {
            depth.enableStencil();                 // same depth format, or the blit fails
        }
        if (depth.width != main.width || depth.height != main.height) {
            depth.resize(main.width, main.height, Minecraft.ON_OSX);
        }
        depth.copyDepthFrom(main);
        GlStateManager._glBindFramebuffer(GL30.GL_READ_FRAMEBUFFER, prevRead);
        GlStateManager._glBindFramebuffer(GL30.GL_DRAW_FRAMEBUFFER, prevDraw);
        copiedFrame = frame;
    }

    /** Sun (or moon) direction and colours. Brightness itself comes from the lightmap (night, caves, gamma). */
    private static void lighting(Minecraft mc, ShaderInstance sh) {
        ClientLevel lv = mc.level;
        float pt = mc.getFrameTime();
        float sx = 0.3f, sy = 0.9f, sz = 0.3f;
        float r = 1.0f, g = 1.0f, b = 1.0f, k = 0.35f;
        if (lv != null && lv.dimensionType().hasSkyLight()) {
            double a = lv.getTimeOfDay(pt) * Math.PI * 2.0;
            sx = (float) -Math.sin(a);
            sy = (float) Math.cos(a);
            if (sy > -0.08f) {
                float warm = 1.0f - Mth.clamp(sy * 3.0f, 0.0f, 1.0f);      // low sun: orange light
                r = 1.06f;
                g = 0.97f - 0.30f * warm;
                b = 0.88f - 0.52f * warm;
                k = Mth.clamp((sy + 0.08f) * 6.0f, 0.0f, 1.0f) * 1.05f;
            } else {
                sx = -sx;
                sy = -sy;
                r = 0.55f;
                g = 0.62f;
                b = 0.86f;
                k = 0.6f;
            }
            k *= 1.0f - 0.75f * lv.getRainLevel(pt);
            sz = 0.28f;                                                     // tilt off the sun plane
        }
        float n = Mth.sqrt(sx * sx + sy * sy + sz * sz);
        sh.safeGetUniform("SunDir").set(sx / n, sy / n, sz / n);
        sh.safeGetUniform("SunCol").set(r * k, g * k, b * k);
        float amb = 0.40f + 0.22f * (1.0f - Math.min(k, 1.0f));
        sh.safeGetUniform("AmbCol").set(amb * 0.94f, amb, amb * 1.08f);
    }

    // ------------------------------------------------------------------ geometry
    /**
     * One puff: 4 vertices. Outside the sphere the quad goes through the centre perpendicular to the view ray and is
     * just big enough for the silhouette; with the camera inside (or touching) it becomes a screen-covering quad right
     * in front of the camera - the shader starts the ray at t = 0 then.
     */
    static void quad(BufferBuilder b, Camera cam, float cx, float cy, float cz, float rad, float r, float g, float bl, float a,
                     int light, float seed, float heat, float dens, float age) {
        int ir = (int) (Mth.clamp(r, 0.0f, 1.0f) * 255.0f);
        int ig = (int) (Mth.clamp(g, 0.0f, 1.0f) * 255.0f);
        int ib = (int) (Mth.clamp(bl, 0.0f, 1.0f) * 255.0f);
        int ia = (int) (Mth.clamp(a, 0.0f, 1.0f) * 255.0f);
        float d2 = cx * cx + cy * cy + cz * cz;
        float px, py, pz, ax, ay, az, ux, uy, uz;
        if (d2 > rad * rad * 1.5625f) {
            float d = Mth.sqrt(d2);
            float rho = rad * d / Mth.sqrt(d2 - rad * rad) * 1.03f;
            float fx = cx / d, fy = cy / d, fz = cz / d;
            float rx = -fz, rz = fx;
            float rl = Mth.sqrt(rx * rx + rz * rz);
            if (rl < 1.0e-3f) {
                rx = 1.0f;
                rz = 0.0f;
                rl = 1.0f;
            }
            rx /= rl;
            rz /= rl;
            ux = rz * fy * -1.0f;               // up = right x forward  (right.y = 0)
            uy = rz * fx - rx * fz;
            uz = rx * fy;
            px = cx;
            py = cy;
            pz = cz;
            ax = rx * rho;
            ay = 0.0f;
            az = rz * rho;
            ux *= rho;
            uy *= rho;
            uz *= rho;
        } else {
            if (++inside > MAX_INSIDE) {
                return;
            }
            Vector3f f = cam.getLookVector();
            Vector3f u = cam.getUpVector();
            Vector3f l = cam.getLeftVector();
            float z0 = 0.3f, s = 2.5f;
            px = f.x() * z0;
            py = f.y() * z0;
            pz = f.z() * z0;
            ax = l.x() * s;
            ay = l.y() * s;
            az = l.z() * s;
            ux = u.x() * s;
            uy = u.y() * s;
            uz = u.z() * s;
        }
        vtx(b, px - ax - ux, py - ay - uy, pz - az - uz, ir, ig, ib, ia, light, cx, cy, cz, rad, seed, heat, dens, age);
        vtx(b, px - ax + ux, py - ay + uy, pz - az + uz, ir, ig, ib, ia, light, cx, cy, cz, rad, seed, heat, dens, age);
        vtx(b, px + ax + ux, py + ay + uy, pz + az + uz, ir, ig, ib, ia, light, cx, cy, cz, rad, seed, heat, dens, age);
        vtx(b, px + ax - ux, py + ay - uy, pz + az - uz, ir, ig, ib, ia, light, cx, cy, cz, rad, seed, heat, dens, age);
    }

    private static void vtx(BufferBuilder b, float x, float y, float z, int r, int g, int bl, int a, int light,
                            float cx, float cy, float cz, float rad, float seed, float heat, float dens, float age) {
        b.vertex(x, y, z);
        b.color(r, g, bl, a);
        b.uv2(light);
        b.putFloat(0, cx);
        b.putFloat(4, cy);
        b.putFloat(8, cz);
        b.putFloat(12, rad);
        b.nextElement();
        b.putFloat(0, seed);
        b.putFloat(4, heat);
        b.putFloat(8, dens);
        b.putFloat(12, age);
        b.nextElement();
        b.endVertex();
    }

    // ------------------------------------------------------------------ spawning helpers
    /**
     * Drop-in for {@code lv.addAlwaysVisibleParticle(type, true, ...)} with vanilla smoke types: spawns the volumetric
     * equivalent while volumetric smoke is on (campfire smoke -> big grey puff, large smoke -> dark puff).
     */
    public static void vanilla(ClientLevel lv, net.minecraft.core.particles.ParticleOptions type, double x, double y, double z, double vx, double vy, double vz) {
        if (on) {
            VSmokeOptions o = VSmokeOptions.vanillaPreset(type, lv.random);   // r28: SMOKE added, presets shared with the server
            if (o != null) {
                puff(lv, x, y, z, vx, vy, vz, o);
                return;
            }
        }
        lv.addAlwaysVisibleParticle(type, true, x, y, z, vx, vy, vz);
    }

    /**
     * r28: {@link #vanilla} for code that only has a {@link net.minecraft.world.level.Level} (entities, blocks). Does
     * nothing on the server: server-side smoke goes through {@link VSmokeOptions#sendVanilla}.
     */
    public static void addVanilla(net.minecraft.world.level.Level lv, net.minecraft.core.particles.ParticleOptions type, double x, double y, double z, double vx, double vy, double vz) {
        if (lv instanceof ClientLevel cl) {
            vanilla(cl, type, x, y, z, vx, vy, vz);
        }
    }

    /** r28: BM-21 / tubombers blast smoke (dark, rises and spreads, 4-7 s) as a volumetric puff; no-op on the server. */
    public static void puffBlast(Level lv, double x, double y, double z, double vx, double vy, double vz) {
        if (lv instanceof ClientLevel cl) {
            puff(cl, x, y, z, vx, vy, vz, new VSmokeOptions(0.2f, 0.19f, 0.18f, 1.2f, 3.0f, 80 + cl.random.nextInt(60), 0.7f, 0.0f, 0.002f));
        }
    }

    /** r28: BM-21 / tubombers smoke-screen wall puff (white-grey, almost static, 12-16 s) as a volumetric puff. */
    public static void puffWall(Level lv, double x, double y, double z, double vx, double vy, double vz) {
        if (lv instanceof ClientLevel cl) {
            puff(cl, x, y, z, vx, vy, vz, new VSmokeOptions(0.8f, 0.8f, 0.79f, 2.2f, 1.4f, 240 + cl.random.nextInt(80), 0.6f, 0.0f, 0.0f));
        }
    }

    /**
     * Generic smoke puff (used by the {@code aiarsenal:vsmoke} particle and by client code): grows from o.size to
     * o.size * o.grow along an ease-out curve, fades in fast and out slowly, drifts with (vx, vy, vz) (blocks/tick,
     * damped) plus o.rise of buoyancy per tick, glows with o.heat during the first 15 % of its life.
     */
    public static FxParticle puff(ClientLevel lv, double x, double y, double z, double vx, double vy, double vz, VSmokeOptions o) {
        int life = Math.max(4, o.life());
        float s0 = Math.max(0.05f, o.size());
        float s1 = s0 * Math.max(0.2f, o.grow());
        float a0 = Mth.clamp(o.alpha(), 0.0f, 1.0f);
        float heat0 = Mth.clamp(o.heat(), 0.0f, 1.0f);
        float rise = o.rise();
        float cr = o.r(), cg = o.g(), cb = o.b();
        FxParticle p = new FxParticle(lv, x, y, z, Sprites.smoke(lv.random.nextInt(4)), life, false, s0);
        p.velocity(vx, vy, vz);
        p.spin = (lv.random.nextFloat() - 0.5f) * 0.02f;
        p.color(cr, cg, cb);
        p.alpha(0.0f);
        p.heat = heat0;
        p.motion = (pp, age) -> {
            float f = (float) age / (float) life;
            pp.translate(pp.getDeltaX(), pp.getDeltaY() + rise, pp.getDeltaZ());
            pp.scaleVelocity(0.96);
            float e = 1.0f - (1.0f - f) * (1.0f - f);
            pp.size = s0 + (s1 - s0) * e;
            float fadeIn = Math.min(1.0f, (float) age / Math.max(2.0f, life * 0.06f));
            float fadeOut = f > 0.55f ? 1.0f - (f - 0.55f) / 0.45f : 1.0f;
            pp.alpha(a0 * fadeIn * fadeOut);
            pp.heat = heat0 * Math.max(0.0f, 1.0f - f / 0.15f);
            float w = pp.heat;
            pp.color(Math.min(1.0f, cr + 0.35f * w), Math.min(1.0f, cg + 0.12f * w), cb);
        };
        FxSystem.add(p);
        return p;
    }
}
