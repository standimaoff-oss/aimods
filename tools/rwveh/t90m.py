# T-90A (r27: was T-90M "Proryv") main battle tank — GunVehicle node contract.
# Nodes: root > hull geo, rw_L_i/rw_R_i, spk_*, idl_*, rr_*_i, track links (clips track_L/track_R),
#        launcher_yaw (turret ring 0,1.47,0.30 glTF) > launcher_pitch (trunnion) > barrel (recoil along -Z glTF)
# Blender: front = -Y, +X = vehicle left.  glTF = (x, z, -y).
reset_scene()
col_get("BUILD"); col_get("RIG")
armor_mats()
amat("M_Dazzler", None, 0.2, 0.0, factor=(0.95, 0.22, 0.04, 1), emissive=(0.85, 0.18, 0.02, 1))
P = "T90"
G = P + "_hull"
GT = P + "_turret"
GG = P + "_gun"
GB = P + "_barrel"
TX = 1.395                      # track centre x
TW = 0.58                       # track width
RR = 0.375                      # road wheel radius
ZW = RR + 0.07                  # road wheel centre height
ROAD = [(-2.15 + k * 0.812, ZW) for k in range(6)]
SPK = (2.86, 0.70)
IDL = (-2.93, 0.62)
ROLL = [(1.25, 0.975), (0.0, 0.985), (-1.25, 0.975)]
TC = Vector((0, -0.30, 1.47))   # turret ring centre
TRN = Vector((0, -1.45, 1.86))  # trunnion
MUZ_Y = -6.20

# ---------------------------------------------------------------- running gear (both sides)
WHEELS = []
LINKS = []
for side, x in (("L", TX), ("R", -TX)):
    W, links, pitch = running_gear(P, side, x, ROAD, RR, SPK, 0.33, IDL, 0.28, ROLL, 0.115, TW, 0.137, 0.05,
                                   style="ru", gap=0.09, teeth=13, mat="M_Body", arm_grp=G)
    WHEELS += W
    LINKS += links
print("TRACK_PITCH", pitch, "LINKS", len(LINKS))
# suspension: torsion-bar arms + bump stops + hydraulic shocks on wheels 1,2,6
for sx in (1, -1):
    for i, (y, z) in enumerate(ROAD):
        rod("%s_arm%d_%d" % (P, sx, i), Vector((sx * 1.10, y + 0.32, z + 0.06)), Vector((sx * 1.22, y, z)), 0.05, "M_Body", G, seg=8)
        abox("%s_bump%d_%d" % (P, sx, i), (0.08, 0.12, 0.1), (sx * 1.12, y + 0.18, z + 0.32), "M_Dark", G, bevel=0.01)
    for i in (0, 1, 5):
        y = ROAD[i][0]
        rod("%s_shock%d_%d" % (P, sx, i), Vector((sx * 1.12, y + 0.25, ZW + 0.08)), Vector((sx * 1.12, y + 0.05, ZW + 0.45)), 0.04, "M_Dark", G, seg=8)
    rod("%s_idlarm%d" % (P, sx), Vector((sx * 1.12, IDL[0] + 0.25, IDL[1] + 0.05)), Vector((sx * 1.25, IDL[0], IDL[1])), 0.07, "M_Body", G, seg=8)
    acyl("%s_fdrv%d" % (P, sx), 0.26, 0.22, (sx * 1.17, SPK[0], SPK[1]), "M_Body", G, axis=0, seg=16)

# ---------------------------------------------------------------- hull
hull_prof = [(-3.00, 0.47), (-3.43, 0.86), (-2.05, 1.44), (2.15, 1.47), (3.43, 1.40), (3.40, 0.64), (2.95, 0.47)]
prism_x(P + "_hull", hull_prof, 1.08, "M_Body", G, bevel=0.03)
# fender shelves over the tracks + front mud flaps
for sx in (1, -1):
    abox("%s_fender%d" % (P, sx), (0.66, 6.5, 0.04), (sx * 1.41, 0.12, 1.16), "M_Body", G, bevel=0.01)
    tilted_box("%s_flap%d" % (P, sx), (sx * 1.41, -3.13, 1.16), (sx * 1.41, -3.42, 0.98), 0.66, 0.025, "M_Rubber", G)
    abox("%s_fendlip%d" % (P, sx), (0.03, 6.5, 0.07), (sx * 1.735, 0.12, 1.15), "M_Body", G, bevel=0.005)
# side skirts: steel panels with Relikt modules on the front half, slat screen over the engine
for sx in (1, -1):
    abox("%s_skirt%d" % (P, sx), (0.025, 6.3, 0.46), (sx * 1.74, 0.05, 0.90), "M_Body", G, bevel=0.006)
    for k in range(6):
        y = -2.85 + k * 0.62
        abox("%s_sera%d_%d" % (P, sx, k), (0.11, 0.58, 0.44), (sx * 1.81, y, 0.92), "M_Body", G, bevel=0.012)
        for j in (-1, 1):
            acyl("%s_serb%d_%d_%d" % (P, sx, k, j), 0.014, 0.014, (sx * 1.87, y + 0.2 * j, 1.08), "M_Steel", G, axis=0, seg=6, dirt=False)
        abox("%s_serh%d_%d" % (P, sx, k), (0.02, 0.4, 0.04), (sx * 1.87, y, 0.78), "M_Dark", G, bevel=0.0)
    # r27 T-90A: rubber skirt flaps over the engine half (no slat screen)
    for k in range(4):
        abox("%s_rskirt%d_%d" % (P, sx, k), (0.02, 0.56, 0.46), (sx * 1.765, 1.05 + k * 0.6, 0.90), "M_Rubber", G, bevel=0.004)
# glacis Relikt rows (plate rises ~22.6 deg towards the rear)
gl0, gl1 = Vector((0, -3.43, 0.86)), Vector((0, -2.05, 1.44))
ang = math.atan2(gl1.z - gl0.z, gl1.y - gl0.y)
nrm = Vector((0, -math.sin(ang), math.cos(ang)))
for r, f in enumerate((0.18, 0.47, 0.76)):
    c = gl0.lerp(gl1, f) + nrm * 0.06
    era_row(P, "g%d" % r, c + Vector((0.92, 0, 0)), c + Vector((-0.92, 0, 0)), 6, (0.3, 0.42, 0.09), (ang, 0, 0), G)
# lower front plate: dozer-blade mount + tow hooks + track-width mine-plough lugs
abox(P + "_lfp_blade", (2.0, 0.06, 0.18), (0, -3.28, 0.62), "M_Body", G, rot=(0.6, 0, 0), bevel=0.01)
for sx in (1, -1):
    lathe_y("%s_hook%d" % (P, sx), [(-0.03, 0.06), (-0.03, 0.1), (0.03, 0.1), (0.03, 0.06)], (sx * 0.75, -3.36, 0.74), ["M_Steel"], G, seg=12, axis='X')
    abox("%s_hookb%d" % (P, sx), (0.1, 0.1, 0.12), (sx * 0.75, -3.3, 0.74), "M_Body", G, bevel=0.01)
# headlights with guards (left: IR + white)
for sx in (1, -1):
    c = Vector((sx * 1.15, -3.08, 1.24))
    acyl("%s_hl%d" % (P, sx), 0.085, 0.12, tuple(c), "M_Dark", G, axis=1, seg=14)
    acyl("%s_hll%d" % (P, sx), 0.07, 0.01, tuple(c + Vector((0, -0.065, 0))), "M_HeadLamp", G, axis=1, seg=14, dirt=False)
    for k in range(3):
        rod("%s_hlg%d_%d" % (P, sx, k), c + Vector((-0.12 + k * 0.12, -0.12, -0.08)), c + Vector((-0.12 + k * 0.12, -0.12, 0.12)), 0.01, "M_Steel", G, seg=5)
# driver hatch + 3 periscopes (centre)
hatch(P, "drv", (0, -2.36, 1.46), 0.27, G)
for k, yaw in enumerate((-0.45, 0.0, 0.45)):
    periscope(P, "drv%d" % k, (math.sin(yaw) * 0.3, -2.62 + abs(yaw) * 0.12, 1.47), G, yaw)
abox(P + "_wiper", (0.5, 0.03, 0.06), (0, -2.72, 1.42), "M_Dark", G, bevel=0.0)
# engine deck: louvers, filler caps, unditching beam, two fuel drums, rear lights, exhaust (left side)
slats(P + "_louv", -0.85, 0.85, 1.55, 2.45, 1.475, 11, "M_Dark", G, along='Y')
slats(P + "_louv2", -0.85, 0.85, 2.7, 3.25, 1.43, 6, "M_Dark", G, along='Y')
for sx in (1, -1):
    acyl("%s_filler%d" % (P, sx), 0.07, 0.04, (sx * 0.75, 1.15, 1.49), "M_Steel", G, seg=12)
log = Vector((0, 3.64, 1.52))
acyl(P + "_log", 0.15, 3.0, tuple(log), "M_Seat", G, axis=0, seg=14)
for sx in (1, -1):
    rod("%s_logch%d" % (P, sx), log + Vector((sx * 1.1, 0, 0.15)), log + Vector((sx * 1.1, -0.25, 0.0)), 0.012, "M_Steel", G, seg=5)
    drum = Vector((sx * 0.62, 3.62, 0.98))
    acyl("%s_drum%d" % (P, sx), 0.29, 0.88, tuple(drum), "M_DarkGreen", G, axis=0, seg=20)
    for dx in (-0.3, 0.0, 0.3):
        acyl("%s_drumr%d_%d" % (P, sx, int(dx * 10)), 0.30, 0.025, tuple(drum + Vector((dx, 0, 0))), "M_DarkGreen", G, axis=0, seg=20)
    abox("%s_drumbr%d" % (P, sx), (0.92, 0.08, 0.06), tuple(drum + Vector((0, -0.25, -0.22))), "M_Body", G, bevel=0.005)
    abox("%s_tail%d" % (P, sx), (0.12, 0.05, 0.08), (sx * 1.25, 3.44, 1.3), "M_Dark", G, bevel=0.005)
    acyl("%s_taill%d" % (P, sx), 0.03, 0.01, (sx * 1.25, 3.47, 1.3), "M_Amber", G, axis=1, seg=8, dirt=False)
    lathe_y("%s_rhook%d" % (P, sx), [(-0.03, 0.06), (-0.03, 0.1), (0.03, 0.1), (0.03, 0.06)], (sx * 0.9, 3.45, 0.72), ["M_Steel"], G, seg=12, axis='X')
abox(P + "_exh", (0.06, 0.6, 0.22), (1.74, 2.55, 1.25), "M_Dark", G, bevel=0.01)
slats(P + "_exhs", 1.765, 1.775, 2.3, 2.8, 1.25, 6, "M_Bore", G, along='Y')
# fender stowage: tool boxes + spare track links + tow cable
for sx in (1, -1):
    for k in range(3):
        abox("%s_box%d_%d" % (P, sx, k), (0.5, 0.7, 0.32), (sx * 1.42, -1.6 + k * 0.85, 1.34), "M_Body", G, bevel=0.015)
        abox("%s_boxl%d_%d" % (P, sx, k), (0.52, 0.72, 0.03), (sx * 1.42, -1.6 + k * 0.85, 1.5), "M_Plain", G, bevel=0.005)
        abox("%s_boxh%d_%d" % (P, sx, k), (0.02, 0.12, 0.03), (sx * 1.68, -1.6 + k * 0.85, 1.42), "M_Steel", G, bevel=0.0)
    for k in range(4):
        abox("%s_spare%d_%d" % (P, sx, k), (0.5, 0.13, 0.04), (sx * 1.4, 1.3 + k * 0.15, 1.2), "M_Track", G, bevel=0.005)
tow_cable(P, "L", (1.15, -2.8, 1.52), (1.15, -0.6, 1.52), 0.02, G)

# ---------------------------------------------------------------- turret (launcher_yaw)
def T(x, y, z):
    return Vector((x, TC.y + y, z))
# r27: T-90A (obr. 2004-2006) welded turret per the reference photos - angular plan view, Kontakt-5 "brow" wedges,
#      Shtora-1 TShU-1-7 IR dazzlers either side of the gun, TShU-1-11 laser warning heads, 902B smoke grenade tubes.
half_b = [(0.0, -1.30), (0.95, -1.18), (1.20, -0.72), (1.22, 0.40), (1.06, 1.04), (0.76, 1.30), (0.0, 1.32)]
half_m = [(0.0, -1.32), (0.98, -1.20), (1.24, -0.72), (1.26, 0.40), (1.09, 1.06), (0.79, 1.32), (0.0, 1.34)]
half_t = [(0.0, -1.04), (0.80, -0.98), (1.08, -0.62), (1.12, 0.40), (0.98, 0.98), (0.72, 1.22), (0.0, 1.24)]
rings = [[T(x, y, z) for x, y in mirror_outline(h)] for h, z in ((half_b, 1.50), (half_m, 1.80), (half_t, 2.20))]
loft_rings(P + "_tshell", rings, "M_Body", GT, bevel=0.025)
lathe_y(P + "_tring", [(0.0, 1.0), (0.0, 1.08), (0.07, 1.08), (0.07, 1.0)], (0, TC.y, 1.47), ["M_Dark"], GT, seg=40, axis='Z')
# weld seams along the plate joints
for sx in (1, -1):
    rod("%s_weld%d" % (P, sx), T(sx * 0.97, -1.20, 1.80), T(sx * 0.80, -0.98, 2.20), 0.012, "M_Body", GT, seg=5)
    rod("%s_weldr%d" % (P, sx), T(sx * 1.25, -0.72, 1.80), T(sx * 1.27, 0.40, 1.80), 0.012, "M_Body", GT, seg=5)
# rear stowage basket (T-90A has no bustle) + OPVT snorkel tube on the rear
for sx in (1, -1):
    rod("%s_bskside%d" % (P, sx), T(sx * 0.95, 1.05, 1.88), T(sx * 0.95, 1.62, 1.88), 0.014, "M_Dark", GT, seg=5)
    rod("%s_bsksidel%d" % (P, sx), T(sx * 0.95, 1.05, 1.62), T(sx * 0.95, 1.62, 1.62), 0.014, "M_Dark", GT, seg=5)
for z in (1.62, 1.88):
    rod("%s_bskrear%d" % (P, int(z * 100)), T(-0.95, 1.62, z), T(0.95, 1.62, z), 0.014, "M_Dark", GT, seg=5)
for k in range(9):
    x = -0.95 + k * 0.2375
    rod("%s_bskv%d" % (P, k), T(x, 1.62, 1.62), T(x, 1.62, 1.88), 0.01, "M_Dark", GT, seg=5)
abox(P + "_bskfloor", (1.9, 0.55, 0.02), tuple(T(0, 1.36, 1.61)), "M_Dark", GT, bevel=0.0)
abox(P + "_bskload", (1.5, 0.42, 0.22), tuple(T(0.05, 1.36, 1.73)), "M_Canvas", GT, bevel=0.04)
acyl(P + "_snork", 0.09, 1.1, tuple(T(0.0, 1.40, 1.98)), "M_DarkGreen", GT, axis=0, seg=14)
# Kontakt-5 wedge "brows" on the turret front: forward-sloping armoured lids with the K-5 cassettes underneath
for sx in (1, -1):
    q = [(sx * 0.34, -1.52), (sx * 1.05, -1.38), (sx * 1.14, -0.80), (sx * 0.34, -0.86)]
    if sx < 0:
        q = list(reversed(q))
    lo = [T(x, y, 1.96) for x, y in q]
    hi = [T(x * 0.98, y + (0.30 if y < -1.0 else 0.0), 2.26) for x, y in q]
    loft_rings("%s_k5brow%d" % (P, sx), [lo, hi], "M_Body", GT, bevel=0.012)
    # cassette lid seams (5 lids per side) + lifting eyes
    for k in range(1, 5):
        f = k / 5.0
        x = sx * (0.34 + 0.75 * f)
        rod("%s_k5seam%d_%d" % (P, sx, k), T(x, -1.47 + 0.11 * f, 1.985), T(x * 0.98, -1.15 + 0.08 * f, 2.27), 0.008, "M_Dark", GT, seg=4)
    for k in range(3):
        acyl("%s_k5bolt%d_%d" % (P, sx, k), 0.018, 0.02, tuple(T(sx * (0.48 + k * 0.25), -1.05, 2.275)), "M_Steel", GT, seg=6, dirt=False)
    # vertical K-5 cassettes on the cheek below the brow (outboard of the dazzler)
    abox("%s_k5cheek%d" % (P, sx), (0.22, 0.16, 0.42), tuple(T(sx * 1.07, -1.27, 1.74)), "M_Body", GT, rot=(0, 0, sx * 0.25), bevel=0.01)
    # --- Shtora-1 TShU-1-7 IR dazzler: armoured box, round orange-red emitter window, sun hood, cable conduit
    D = T(sx * 0.70, -1.39, 1.78)
    abox("%s_tshu%d" % (P, sx), (0.34, 0.30, 0.34), tuple(D), "M_Body", GT, bevel=0.025)
    abox("%s_tshub%d" % (P, sx), (0.26, 0.12, 0.26), tuple(D + Vector((0, 0.19, 0))), "M_Body", GT, bevel=0.01)
    acyl("%s_tshur%d" % (P, sx), 0.135, 0.05, tuple(D + Vector((0, -0.165, 0))), "M_Dark", GT, axis=1, seg=24)
    acyl("%s_tshul%d" % (P, sx), 0.115, 0.012, tuple(D + Vector((0, -0.192, 0))), "M_Dazzler", GT, axis=1, seg=24, dirt=False)
    abox("%s_tshuh%d" % (P, sx), (0.36, 0.10, 0.025), tuple(D + Vector((0, -0.20, 0.175))), "M_Body", GT, rot=(-0.25, 0, 0), bevel=0.005)
    rod("%s_tshuc%d" % (P, sx), D + Vector((sx * 0.17, 0.05, -0.1)), D + Vector((sx * 0.30, 0.18, -0.12)), 0.02, "M_Dark", GT, seg=6)
    # TShU-1-11 coarse laser-warning heads on the front roof corners (blue window) + precise head on a stalk
    W = T(sx * 1.00, -0.62, 2.24)
    abox("%s_lwsc%d" % (P, sx), (0.14, 0.12, 0.09), tuple(W), "M_Dark", GT, bevel=0.012)
    abox("%s_lwscw%d" % (P, sx), (0.10, 0.012, 0.06), tuple(W + Vector((0, -0.065, 0.005))), "M_Lens", GT, bevel=0.0, dirt=False)
    # 902B Tucha smoke grenade launchers: 6 tubes per side on the turret flanks, fanned forward/outward
    smoke_dischargers(P, "s%d" % sx, T(sx * 1.17, -0.30, 2.12), 6, 7.0, sx * 25.0, 15.0, GT, r=0.042, L=0.24)
    # side stowage boxes behind the launchers
    abox("%s_tbox%d" % (P, sx), (0.22, 0.75, 0.36), tuple(T(sx * 1.30, 0.55, 1.82)), "M_Body", GT, bevel=0.015)
# Shtora control box + precise TShU-1-11 heads at the rear roof
for sx in (1, -1):
    rod("%s_lwsps%d" % (P, sx), T(sx * 0.35, 0.95, 2.18), T(sx * 0.35, 0.95, 2.36), 0.015, "M_Dark", GT, seg=6)
    acyl("%s_lwsp%d" % (P, sx), 0.06, 0.07, tuple(T(sx * 0.35, 0.95, 2.39)), "M_Dark", GT, seg=12)
    acyl("%s_lwspw%d" % (P, sx), 0.045, 0.01, tuple(T(sx * 0.35, 0.95, 2.43)), "M_Lens", GT, seg=12, dirt=False)
abox(P + "_shtcb", (0.32, 0.22, 0.12), tuple(T(0.0, 0.70, 2.25)), "M_Body", GT, bevel=0.012)
# mantlet + dust cover
abox(P + "_mantf", (0.56, 0.22, 0.48), tuple(T(0, -1.36, 1.86)), "M_Body", GT, bevel=0.03)
# gunner's 1G46 day sight (left front roof) with armoured door; blue window
S = T(0.42, -0.86, 2.36)
abox(P + "_sosna", (0.30, 0.42, 0.30), tuple(S), "M_Body", GT, bevel=0.02)
abox(P + "_sosnaw", (0.22, 0.02, 0.16), tuple(S + Vector((0, -0.22, 0.02))), "M_Lens", GT, bevel=0.0, dirt=False)
abox(P + "_sosnad", (0.26, 0.03, 0.06), tuple(S + Vector((0, -0.20, 0.17))), "M_Body", GT, rot=(-0.6, 0, 0), bevel=0.005)
# Buran-PA / Essa gunner's night sight box behind it
abox(P + "_buran", (0.24, 0.30, 0.22), tuple(T(0.70, -0.55, 2.31)), "M_Body", GT, bevel=0.015)
acyl(P + "_buranw", 0.06, 0.01, tuple(T(0.70, -0.71, 2.33)), "M_Lens", GT, axis=1, seg=12, dirt=False)
hatch(P, "gnr", T(0.48, -0.15, 2.21), 0.28, GT)
# commander's TKN-4S cupola (right) with the remote 12.7 mm Kord (UDP T05BV-1) on its own box
C = T(-0.52, -0.15, 2.21)
lathe_y(P + "_cup", [(0.0, 0.0), (0.0, 0.42), (0.16, 0.38), (0.16, 0.0)], tuple(C), ["M_Body"], GT, seg=28, axis='Z')
acyl(P + "_cuplid", 0.32, 0.05, tuple(C + Vector((0, 0.05, 0.19))), "M_Body", GT, seg=24)
for k in range(5):
    a = math.radians(-60 + k * 30)
    periscope(P, "cup%d" % k, C + Vector((math.sin(a) * 0.38, -math.cos(a) * 0.38, 0.12)), GT, a)
tkn = C + Vector((0.0, -0.40, 0.24))
abox(P + "_tkn", (0.26, 0.22, 0.20), tuple(tkn), "M_Body", GT, bevel=0.015)
abox(P + "_tknw", (0.18, 0.02, 0.09), tuple(tkn + Vector((0, -0.12, 0.02))), "M_Lens", GT, bevel=0.0, dirt=False)
rws = C + Vector((0.05, 0.25, 0.32))
abox(P + "_rwsb", (0.36, 0.36, 0.22), tuple(rws), "M_Body", GT, bevel=0.02)
acyl(P + "_kord", 0.022, 1.25, tuple(rws + Vector((0.08, -0.75, 0.08))), "M_Dark", GT, axis=1, seg=10)
acyl(P + "_kordfh", 0.035, 0.12, tuple(rws + Vector((0.08, -1.38, 0.08))), "M_Dark", GT, axis=1, seg=10)
abox(P + "_kordr", (0.12, 0.4, 0.14), tuple(rws + Vector((0.08, -0.05, 0.1))), "M_Dark", GT, bevel=0.01)
abox(P + "_kordbox", (0.14, 0.26, 0.2), tuple(rws + Vector((-0.17, 0.0, 0.05))), "M_DarkGreen", GT, bevel=0.01)
# meteo mast, two antennas
rod(P + "_mast", T(-0.15, 0.9, 2.2), T(-0.15, 0.9, 2.62), 0.015, "M_Dark", GT, seg=6)
acyl(P + "_mastv", 0.04, 0.06, tuple(T(-0.15, 0.9, 2.65)), "M_Dark", GT, seg=8)
antenna(P, "a1", T(0.85, 0.82, 2.2), 2.4, GT)
antenna(P, "a2", T(-0.85, 0.82, 2.2), 1.2, GT)

# ---------------------------------------------------------------- gun (launcher_pitch) + barrel (recoils)
abox(P + "_cradle", (0.5, 0.75, 0.42), (0, TRN.y + 0.15, TRN.z), "M_Body", GG, bevel=0.02)
abox(P + "_mantm", (0.46, 0.22, 0.4), (0, TRN.y - 0.25, TRN.z), "M_Body", GG, bevel=0.03)
lathe_y(P + "_dustc", [(0.0, 0.17), (0.12, 0.2), (0.24, 0.15)], (0, TRN.y - 0.36, TRN.z), ["M_Canvas"], GG, seg=16, axis='Y')
acyl(P + "_coax", 0.018, 0.25, (0.28, TRN.y - 0.42, TRN.z - 0.06), "M_Dark", GG, axis=1, seg=8)
gun_tube(P, GB, TRN.y - 0.30, MUZ_Y, TRN.z, 0.085, 0.13, mat="M_Body", sleeve=True, evac=(TRN.y - 2.25, 0.16, 0.62), mrs=True)

# ---------------------------------------------------------------- hierarchy + export
# r5: every part must touch its node body (smoke dischargers, skirts, brackets, handwheels ...)
auto_attach([G, GT, GG, GB], bracket_groups=(GB,))
weather(gen_weather([(1.74, 2.55, 1.25)], 0.9))
rt = root("root")
group_under(G, P + "_hull_geo", rt)
track_rig(rt, P, "", WHEELS)
for o in LINKS:
    attach(o, rt)
ty = pivot("launcher_yaw", tuple(TC), rt)
group_under(GT, "launcher_yaw_geo", ty)
gp = pivot("launcher_pitch", tuple(TRN), ty)
group_under(GG, "launcher_pitch_geo", gp)
br = pivot("barrel", tuple(TRN), gp)
group_under(GB, "barrel_geo", br)
rw_export("/home/user/.cache/rwveh/raw/rw_t90m.glb", "/home/user/models/rw_t90m.blend", "RW_T90M")
