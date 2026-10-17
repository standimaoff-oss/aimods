#!/usr/bin/env python3
"""Deterministically build the WWI Gewehr 98 GLB and small item icon using stdlib-only geometry."""
from __future__ import annotations
import math, random, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from glb_builder import GlbBuilder,Mesh,axis_quaternion,png_rgba
ASSETS=ROOT/"mods/aiarsenal/src/main/resources/assets/aiarsenal"
MODEL_DIR=ASSETS/"models/glb"
TEXTURE_DIR=ASSETS/"textures/entity/gewehr98"
ITEM_DIR=ASSETS/"textures/item"


def stock_texture():
    rng=random.Random(1898)
    w,h=128,64
    p=[]
    for y in range(h):
        for x in range(w):
            grain=int(6*math.sin(x*.19+math.sin(y*.13))+3*math.sin(x*.055+y*.31))+rng.randrange(-4,5)
            base=(119,77,42)
            p.append(tuple(max(0,min(255,c+grain)) for c in base)+(255,))
    return png_rgba(w,h,p)


def item_icon():
    w=h=64;p=[(0,0,0,0)]*(w*h)
    def poly(points,color):
        for y in range(max(0,int(min(q[1] for q in points))),min(h,int(max(q[1] for q in points))+1)):
            for x in range(max(0,int(min(q[0] for q in points))),min(w,int(max(q[0] for q in points))+1)):
                inside=False;j=len(points)-1
                for i,(xi,yi) in enumerate(points):
                    xj,yj=points[j]
                    if (yi>y+.5)!=(yj>y+.5) and x+.5<(xj-xi)*(y+.5-yi)/((yj-yi) or 1e-9)+xi:inside=not inside
                    j=i
                if inside:p[y*w+x]=(color[0],color[1],color[2],255)
    wood=(133,88,48);dark=(48,52,50);steel=(100,110,108);brass=(184,143,64)
    poly(((4,35),(8,33),(20,33),(24,31),(38,31),(43,33),(60,33),(60,35),(43,36),(39,37),(25,37),(22,39),(11,39),(10,37),(4,37)),dark)
    poly(((4,36),(12,36),(14,40),(10,42),(7,41),(6,38),(4,38)),wood)
    poly(((12,34),(21,34),(25,33),(39,33),(43,34),(43,36),(25,36),(22,38),(13,38)),wood)
    poly(((21,32),(40,32),(43,33),(23,34),(18,35),(15,35),(15,34)),steel)
    poly(((40,33),(59,33),(60,34),(43,35)),steel)
    poly(((30,30),(34,30),(34,33),(30,33)),steel)
    poly(((43,31),(45,31),(45,33),(43,33)),steel)
    poly(((24,36),(26,36),(27,40),(25,40)),dark)
    poly(((24,39),(28,39),(28,40),(24,40)),dark)
    for x in (19,22,27,31,35,39):poly(((x,34),(x+1,34),(x+1,35),(x,35)),brass)
    return png_rgba(w,h,p)


def main_mesh(wood,steel,dark,brass):
    m=Mesh()
    # Walnut stock: butt, comb, wrist, grip and handguard. The separate stepped forms preserve the long 1898 silhouette.
    m.box(wood,(-.048,-.045,-.49),(.048,.052,-.28))
    m.box(wood,(-.040,-.055,-.30),(.040,.040,-.08))
    m.box(wood,(-.036,-.052,-.12),(.036,.012,.015))
    m.box(wood,(-.040,-.058,-.04),(.040,.028,.12))
    m.box(wood,(-.033,-.040,.11),(.033,-.003,.37))
    # Buttplate / stock band and the handguard-to-stock ferrules.
    m.box(dark,(-.050,-.048,-.495),(.050,.055,-.475))
    for z in (-.29,-.045,.105,.34):
        m.box(brass,(-.041,-.055,z),(.041,.035,z+.012))
    # Receiver ring, bridge, floorplate and trigger guard.
    m.box(steel,(-.037,-.014,-.085),(.037,.051,.165))
    m.box(dark,(-.041,-.022,-.10),(.041,-.012,.17))
    m.box(steel,(-.040,.050,-.075),(.040,.067,.135))
    m.box(dark,(-.026,-.065,-.055),(.026,-.052,.085))
    m.box(dark,(-.027,-.052,-.058),(-.020,-.026,.086))
    m.box(dark,(.020,-.052,-.058),(.027,-.026,.086))
    m.box(dark,(-.027,-.052,.078),(.027,-.026,.086))
    # Trigger and magazine floorplate.
    m.oriented_box(steel,(0,-.050,.020),(.006,0,0),(0,.015,0),(0,0,.012))
    m.box(steel,(-.030,-.071,.09),(.030,-.053,.155))
    # Long 7.92 mm barrel, receiver shank, front band and muzzle crown.
    m.cylinder(steel,(0,.022,.125),(0,.022,.710),.012,12,steel)
    m.cylinder(dark,(0,.022,.68),(0,.022,.725),.017,12,dark)
    m.cylinder(steel,(0,.022,.708),(0,.022,.721),.013,12,steel)
    # Rear sight base, tangent leaf, adjustable notch and protected front blade.
    m.box(steel,(-.028,.064,.175),(.028,.091,.235))
    m.box(dark,(-.018,.087,.195),(.018,.145,.218))
    m.box(steel,(-.026,.142,.203),(.026,.153,.224))
    m.box(steel,(-.012,.066,.635),(.012,.113,.653))
    m.box(dark,(-.027,.105,.632),(.027,.112,.664))
    # Sling swivels, front band screws, bolt stop and stock checkering panels.
    m.box(dark,(-.010,-.058,-.40),(.010,-.036,-.36))
    m.box(dark,(-.010,-.058,.30),(.010,-.036,.34))
    for x in (-.042,.042):
        m.cylinder(brass,(x,.025,-.26),(x*1.08,.025,-.26),.007,6,brass)
        m.cylinder(brass,(x,.025,.105),(x*1.08,.025,.105),.007,6,brass)
    for i in range(6):
        z=-.18+i*.055
        m.box(dark,(-.037,-.060,z),(-.034,-.057,z+.021))
        m.box(dark,(.034,-.060,z),(.037,-.057,z+.021))
    return m


def bolt_mesh(steel,dark):
    m=Mesh()
    m.cylinder(steel,(-.034,0,0),(.034,0,0),.010,10,steel)
    m.box(dark,(-.035,-.012,-.010),(.035,.012,.010))
    m.cylinder(steel,(.025,0,0),(.057,0,0),.009,8,steel)
    m.oriented_box(dark,(.056,0,0),(.009,0,0),(0,.008,0),(0,0,.020))
    return m


def clip_mesh(brass,steel):
    m=Mesh()
    # Five pointed cartridges retained in a thin stripper clip; exposed only during the reload animation.
    for i in range(5):
        x=(i-2)*.012
        m.cylinder(brass,(x,-.018,-.020),(x,-.018,.020),.0035,6,brass)
        m.cylinder(steel,(x,-.018,.014),(x,-.018,.022),.0045,6,steel)
    m.box(steel,(-.033,-.022,-.021),(.033,-.017,.021))
    return m


def round_mesh(brass,steel):
    m=Mesh();m.cylinder(brass,(0,0,-.018),(0,0,.018),.004,8,brass)
    m.cylinder(steel,(0,0,.014),(0,0,.026),.0045,8,steel);return m


def flash_mesh(brass):
    m=Mesh()
    # Tiny radial flash, hidden for all but the brief shot event by GunRenderer.
    for i in range(8):
        a=math.tau*i/8
        u=(math.cos(a),math.sin(a),0);v=(-math.sin(a),math.cos(a),0)
        c=(0,0,0)
        p1=(u[0]*.020+v[0]*.006,u[1]*.020+v[1]*.006,.015)
        p2=(u[0]*.020-v[0]*.006,u[1]*.020-v[1]*.006,.015)
        tip=(u[0]*.075,u[1]*.075,.015)
        m.triangle(brass,c,p1,tip);m.triangle(brass,c,tip,p2)
    return m


def main():
    TEXTURE_DIR.mkdir(parents=True,exist_ok=True);ITEM_DIR.mkdir(parents=True,exist_ok=True)
    tex=stock_texture();(TEXTURE_DIR/"walnut.png").write_bytes(tex)
    (ITEM_DIR/"gewehr98.png").write_bytes(item_icon())
    b=GlbBuilder("Gewehr 98 infantry rifle (1898 pattern, WWI use)")
    b.add_texture(tex,"gewehr98_walnut_and_steel")
    wood=b.add_material("oiled walnut stock",(1.0,.84,.64,1),.02,.78)
    steel=b.add_material("blued barrel and receiver",(.68,.74,.72,1),.78,.34)
    dark=b.add_material("blackened fittings",(.43,.46,.44,1),.72,.44)
    brass=b.add_material("brass case and fasteners",(.95,.72,.34,1),.68,.35)
    main_i=b.add_mesh("gewehr98_stock_receiver_barrel",main_mesh(wood,steel,dark,brass))
    bolt_i=b.add_mesh("gewehr98_bolt_mesh",bolt_mesh(steel,dark))
    clip_i=b.add_mesh("gewehr98_stripper_clip_mesh",clip_mesh(brass,steel))
    round_i=b.add_mesh("gewehr98_chambered_round_mesh",round_mesh(brass,steel))
    flash_i=b.add_mesh("gewehr98_muzzle_flash_mesh",flash_mesh(brass))
    root=b.add_node("gewehr98")
    body=b.add_node("gewehr98.body",main_i)
    bolt=b.add_node("gewehr98.bolt",bolt_i,(0,.042,.045))
    clip=b.add_node("gewehr98.clip",clip_i,(0,.118,.065))
    bullet=b.add_node("gewehr98.round",round_i,(0,.069,.075))
    flash=b.add_node("gewehr98.flash",flash_i,(0,.022,.726))
    sight=b.add_node("gewehr98.sight",translation=(0,.153,.210))
    arm_r=b.add_node("gewehr98.arm_r",translation=(0,-.040,-.050))
    arm_l=b.add_node("gewehr98.arm_l",translation=(0,-.035,.318))
    b.set_children(root,[body,bolt,clip,bullet,flash,sight,arm_r,arm_l])
    # Bolt cycle: lift, draw the bolt rearward, then return/lock. Times are seconds and match GunClient's shot clock.
    q0=axis_quaternion((0,0,1),0);q1=axis_quaternion((0,0,1),.55);q2=axis_quaternion((0,0,1),.55);q3=q0
    b.add_animation("gewehr98_bolt",[
        (bolt,"translation",[0,.10,.25,.38],[0,.042,.045, 0,.042,-.060, 0,.042,-.060, 0,.042,.045]),
        (bolt,"rotation",[0,.10,.25,.38],[*q0,*q1,*q2,*q3]),
    ])
    # Reload = open bolt, press the five-round clip, discard the clip and close the bolt (2.5 s = 50 ticks).
    up=axis_quaternion((1,0,0),-.42);down=axis_quaternion((1,0,0),0)
    b.add_animation("gewehr98_reload",[
        (bolt,"translation",[0,.24,.42,1.75,2.08,2.50],[0,.042,.045, 0,.042,-.060, 0,.042,-.060, 0,.042,-.060, 0,.042,.045, 0,.042,.045]),
        (bolt,"rotation",[0,.24,.42,1.75,2.08,2.50],[*down,*up,*up,*up,*down,*down]),
        (clip,"translation",[0,.24,.55,1.72,2.05,2.50],[0,.118,.065, 0,.145,.065, 0,.078,.065, 0,.078,.065, 0,.118,.065, 0,.118,.065]),
        (clip,"rotation",[0,.24,.55,1.72,2.05,2.50],[*down,*up,*down,*down,*up,*down]),
    ])
    path=MODEL_DIR/"gewehr98.glb";b.save(path,[root])
    triangles=sum(b.accessors[p["indices"]]["count"]//3 for mesh in b.meshes for p in mesh["primitives"])
    print(f"{path}: {path.stat().st_size:,} bytes; {triangles:,} triangles; embedded walnut/steel texture; 2 clips")

if __name__=="__main__":main()
