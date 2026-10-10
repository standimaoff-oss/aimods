package ru.aiforge.realwar.grenade;

/**
 * r27: hand grenade types. Fuse in ticks (20 = 1 s). {@code kg}/{@code frag} feed ConventionalBlast (HE / fragmentation),
 * {@code fire} the incendiary radius, {@code rgb} the smoke colour (multiplied by the lit smoke shading on the client).
 */
public enum GrenadeKind {
    RGD5("grenade_rgd5", Effect.HE, 60, 0.11, 0.9, 0, 0.0f, 0.0f, 0.0f),
    F1("grenade_f1", Effect.FRAG, 80, 0.06, 2.2, 0, 0.0f, 0.0f, 0.0f),
    FLASHBANG("grenade_flashbang", Effect.FLASH, 40, 0.0, 0.0, 0, 0.0f, 0.0f, 0.0f),
    SMOKE_WHITE("grenade_smoke_white", Effect.SMOKE, 40, 0.0, 0.0, 0, 0.92f, 0.92f, 0.90f),
    SMOKE_RED("grenade_smoke_red", Effect.SMOKE, 40, 0.0, 0.0, 0, 0.78f, 0.12f, 0.08f),
    SMOKE_GREEN("grenade_smoke_green", Effect.SMOKE, 40, 0.0, 0.0, 0, 0.16f, 0.62f, 0.18f),
    SMOKE_BLUE("grenade_smoke_blue", Effect.SMOKE, 40, 0.0, 0.0, 0, 0.14f, 0.32f, 0.82f),
    INCENDIARY("grenade_incendiary", Effect.FIRE, 40, 0.02, 0.5, 2, 0.0f, 0.0f, 0.0f);

    /** what the grenade does when it goes off */
    public enum Effect { HE, FRAG, FLASH, SMOKE, FIRE }

    public final String id;
    public final Effect effect;
    public final int fuse;
    public final double kg;
    public final double frag;
    public final int fire;
    public final float r, g, b;

    GrenadeKind(String id, Effect effect, int fuse, double kg, double frag, int fire, float r, float g, float b) {
        this.id = id;
        this.effect = effect;
        this.fuse = fuse;
        this.kg = kg;
        this.frag = frag;
        this.fire = fire;
        this.r = r;
        this.g = g;
        this.b = b;
    }
}
