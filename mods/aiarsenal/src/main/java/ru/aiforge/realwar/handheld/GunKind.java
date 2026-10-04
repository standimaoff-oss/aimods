package ru.aiforge.realwar.handheld;

/**
 * r22 small arms, real data:
 *  AK-12 (6P70, 2018): 5.45x39, 945 mm (stock extended), barrel 415 mm, 700 rds/min, 900 m/s, 6L31 30-rd magazine.
 *  M4A1: 5.56x45, 838 mm, barrel 368 mm (14.5"), 700-950 rds/min, 880-910 m/s, STANAG 30-rd, Aimpoint CompM4.
 *  RPG-7V2: 40 mm tube, PG-7VL 93 mm HEAT (~600 mm RHA), 6.3 kg, 200 m point-blank / 500 m aimed with the PGO-7V3.
 * Speeds in m/s (1 block = 1 m); spreads are cone half-angles in radians; recoil in degrees per shot; reload in ticks.
 */
public enum GunKind {
    //    id      ammo item     cap  rpm  m/s   dmg   pen   hip     ads      rcP    rcY   rld rldE adsFov sound       auto
    AK12("ak12", "mag_ak12", 30, 700, 900, 7.5f, 7.0f, 0.030f, 0.0016f, 0.95f, 0.40f, 50, 63, 0.80f, "rifle_ak", true),
    M4A1("m4a1", "mag_stanag", 30, 800, 890, 7.0f, 6.0f, 0.028f, 0.0012f, 0.80f, 0.35f, 47, 53, 0.70f, "rifle_m4", true),
    RPG7("rpg7", "pg7v", 1, 0, 0, 0f, 0f, 0.020f, 0.0040f, 4.0f, 1.0f, 70, 70, 0.25f, "", false),     // PGO-7V3 4x (irons 0.8)
    // r23: ORSIS T-5000M .338 LM (bolt action, 700 mm barrel, 5 rds, ~905 m/s, 1 MOA) and PKP Pecheneg (7.62x54R,
    // 650 rds/min, 825 m/s, 100-rd belt box, full-auto only, open bolt)
    T5000("t5000", "mag_t5000", 5, 40, 905, 24f, 18f, 0.060f, 0.0003f, 4.5f, 0.9f, 60, 76, 0.125f, "rifle_t5000", false),
    PKP("pkp", "box_pkp", 100, 650, 825, 11f, 10f, 0.045f, 0.0025f, 1.05f, 0.55f, 120, 130, 0.80f, "mg_pkp", true);

    public final String id, ammo, sound;
    public final int cap, rpm, reload, reloadEmpty;
    public final float speed, damage, pen, hipSpread, adsSpread, recoilPitch, recoilYaw, adsFov;
    public final boolean auto;

    GunKind(String id, String ammo, int cap, int rpm, float speed, float damage, float pen, float hip, float ads, float rcP, float rcY,
            int reload, int reloadEmpty, float adsFov, String sound, boolean auto) {
        this.id = id;
        this.ammo = ammo;
        this.cap = cap;
        this.rpm = rpm;
        this.speed = speed;
        this.damage = damage;
        this.pen = pen;
        this.hipSpread = hip;
        this.adsSpread = ads;
        this.recoilPitch = rcP;
        this.recoilYaw = rcY;
        this.reload = reload;
        this.reloadEmpty = reloadEmpty;
        this.adsFov = adsFov;
        this.sound = sound;
        this.auto = auto;
    }

    public boolean launcher() {
        return this == RPG7;
    }

    /** manual bolt: one aimed shot, then the bolt is cycled (~1.3 s) */
    public boolean boltAction() {
        return this == T5000;
    }

    /** fire selector (B): AK-12 / M4A1; the PKP is full-auto only */
    public boolean selector() {
        return this.auto && this != PKP;
    }

    /** closed-bolt guns keep a round in the chamber on a tactical reload; the belt-fed PKP fires from an open bolt */
    public boolean closedBolt() {
        return !this.launcher() && this != PKP;
    }

    /** variable-power riflescope overlay (T-5000: 5-25x) */
    public boolean scope() {
        return this == T5000;
    }

    /** rifles keep one round in the chamber on a tactical reload (30 + 1) */
    public int maxLoaded(boolean chambered) {
        return this.closedBolt() ? this.cap + (chambered ? 1 : 0) : this.cap;
    }

    /** shots per tick at the cyclic rate */
    public float perTick() {
        return this.rpm / 1200f;
    }

    public static GunKind byOrdinal(int i) {
        GunKind[] v = values();
        return v[Math.max(0, Math.min(v.length - 1, i))];
    }
}
