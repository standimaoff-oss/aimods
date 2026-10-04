package ru.aiforge.realwar.handheld;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.event.level.LevelEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.registries.ForgeRegistries;
import ru.aiforge.realwar.blast.ModDamage;
import ru.aiforge.realwar.damage.HitContext;
import ru.aiforge.realwar.network.GunFxPacket;
import ru.aiforge.realwar.network.ModNetwork;

/**
 * Server side of the r22 small arms: trigger state, cyclic rate, fire selector, magazine reloads and the bullets
 * (point-mass flight at the real muzzle velocity with gravity and light drag; vehicles are hit by their real shape).
 */
@Mod.EventBusSubscriber(modid = "aiarsenal", bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class Firearms {
    public static final int TRIGGER_DOWN = 1, TRIGGER_UP = 2, AIM_ON = 3, AIM_OFF = 4, RELOAD = 5, MODE = 6;
    /** 1 bullet = 1 tick of flight: 9.81 m/s^2 -> blocks/tick^2 */
    private static final double G = 9.81 / 400.0;
    private static final double DRAG = 0.9985;
    private static final int LIFE = 60;

    private static final Map<UUID, State> STATES = new HashMap<>();
    private static final Map<ServerLevel, List<Bullet>> BULLETS = new IdentityHashMap<>();

    private Firearms() {
    }

    static final class State {
        boolean trigger, aiming, semiDone, dryDone;
        float credit;
        int reload, reloadTotal, cooldown;
        boolean reloadEmpty;
        Item gun;
    }

    static final class Bullet {
        Vec3 pos, vel, origin;
        int owner, age;
        float dmg, pen;
    }

    private static State st(Player p) {
        return STATES.computeIfAbsent(p.getUUID(), k -> new State());
    }

    public static boolean reloading(Player p) {
        State s = STATES.get(p.getUUID());
        return s != null && s.reload > 0;
    }

    // ------------------------------------------------------------------ input

    public static void handle(ServerPlayer p, int action) {
        ItemStack stack = p.getMainHandItem();
        if (!(stack.getItem() instanceof FirearmItem g) || p.isSpectator() || p.getVehicle() != null) return;
        State s = st(p);
        switch (action) {
            case TRIGGER_DOWN -> {
                s.trigger = true;
                s.semiDone = false;
                s.dryDone = false;
            }
            case TRIGGER_UP -> s.trigger = false;
            case AIM_ON -> s.aiming = true;
            case AIM_OFF -> s.aiming = false;
            case RELOAD -> startReload(p, stack, g.kind, s);
            case MODE -> {
                if (g.kind.selector() && s.reload == 0) {
                    FirearmItem.setMode(stack, 1 - FirearmItem.mode(stack));
                    sound(p, "selector", 0.6f, 1.0f);
                    fx(p, GunFxPacket.MODE, FirearmItem.ammo(stack));
                }
            }
            default -> {
            }
        }
    }

    // ------------------------------------------------------------------ reload

    /** fullest magazine (or PG-7VL) in the inventory, -1 none */
    static int findAmmo(Player p, GunKind k) {
        Item want = ammoItem(k);
        int best = -1, bestR = 0;
        for (int i = 0; i < p.getInventory().getContainerSize(); i++) {
            ItemStack s = p.getInventory().getItem(i);
            if (!s.is(want)) continue;
            int r = k.launcher() ? 1 : MagazineItem.rounds(s);
            if (r > bestR) {
                best = i;
                bestR = r;
            }
        }
        return best;
    }

    public static Item ammoItem(GunKind k) {
        return ForgeRegistries.ITEMS.getValue(new net.minecraft.resources.ResourceLocation("aiarsenal", k.ammo));
    }

    public static boolean startReload(Player p, ItemStack stack, GunKind k, State s) {
        if (s.reload > 0) return false;
        int ammo = FirearmItem.ammo(stack);
        if (ammo >= k.maxLoaded(ammo > 0)) return false;
        if (!p.getAbilities().instabuild && findAmmo(p, k) < 0) {
            p.displayClientMessage(net.minecraft.network.chat.Component.translatable("msg.aiarsenal.gun.no_mag",
                    net.minecraft.network.chat.Component.translatable("item.aiarsenal." + k.ammo)), true);
            return false;
        }
        s.reloadEmpty = ammo == 0;
        s.reloadTotal = s.reloadEmpty ? k.reloadEmpty : k.reload;
        s.reload = s.reloadTotal;
        s.trigger = false;
        s.gun = stack.getItem();
        sound(p, k.launcher() ? "mag_out" : "mag_out", 0.7f, k.launcher() ? 0.7f : 1.0f);
        fx(p, s.reloadEmpty && !k.launcher() ? GunFxPacket.RELOAD_EMPTY : GunFxPacket.RELOAD, ammo);
        return true;
    }

    /** Gametest / tick: completes the reload: takes the fullest magazine, returns the old one with its rounds. */
    public static void finishReload(Player p, ItemStack stack, GunKind k) {
        int ammo = FirearmItem.ammo(stack);
        boolean creative = p.getAbilities().instabuild;
        int slot = findAmmo(p, k);
        if (k.launcher()) {
            if (slot >= 0 && !creative) p.getInventory().getItem(slot).shrink(1);
            else if (slot < 0 && !creative) return;
            FirearmItem.setAmmo(stack, 1);
            return;
        }
        int load;
        if (slot >= 0 && !creative) {
            ItemStack mag = p.getInventory().getItem(slot);
            Item magItem = mag.getItem();
            load = MagazineItem.rounds(mag);
            mag.shrink(1);
            int keep = k.closedBolt() ? Math.max(0, ammo - 1) : ammo;   // one stays in the chamber (not on the belt-fed PKP)
            ItemStack old = MagazineItem.withRounds(magItem, keep);
            if (!p.getInventory().add(old)) p.drop(old, false);
        } else if (creative) {
            load = k.cap;
        } else {
            return;
        }
        FirearmItem.setAmmo(stack, load + (k.closedBolt() && ammo > 0 ? 1 : 0));
    }

    // ------------------------------------------------------------------ tick

    @SubscribeEvent
    public static void playerTick(TickEvent.PlayerTickEvent e) {
        if (e.phase != TickEvent.Phase.END || !(e.player instanceof ServerPlayer p)) return;
        State s = STATES.get(p.getUUID());
        if (s == null) return;
        ItemStack stack = p.getMainHandItem();
        if (!(stack.getItem() instanceof FirearmItem g) || p.getVehicle() != null || !p.isAlive()) {
            if (s.reload > 0) fx(p, GunFxPacket.CANCEL, 0);
            s.reload = 0;
            s.trigger = false;
            s.aiming = false;
            s.credit = 0;
            return;
        }
        GunKind k = g.kind;
        if (s.reload > 0) {
            if (s.gun != stack.getItem()) {
                s.reload = 0;
                fx(p, GunFxPacket.CANCEL, FirearmItem.ammo(stack));
                return;
            }
            int done = s.reloadTotal - s.reload;
            if (!k.launcher() && done == (int) (s.reloadTotal * 0.55f)) sound(p, "mag_in", 0.8f, k == GunKind.PKP ? 0.75f : 1.0f);
            if (k == GunKind.PKP && (done == 14 || done == (int) (s.reloadTotal * 0.80f))) sound(p, "selector", 0.9f, 0.6f);   // feed cover
            if (k.launcher() && done == (int) (s.reloadTotal * 0.6f)) sound(p, "mag_in", 0.8f, 0.6f);
            if (s.reloadEmpty && !k.launcher() && !k.boltAction() && done == (int) (s.reloadTotal * (k == GunKind.PKP ? 0.86f : 0.82f))) sound(p, "bolt_rack", 0.8f, k == GunKind.PKP ? 0.8f : 1.0f);
            if (s.reloadEmpty && k.boltAction() && done == (int) (s.reloadTotal * 0.68f)) sound(p, "bolt_cycle", 0.8f, 1.0f);
            if (--s.reload == 0) {
                finishReload(p, stack, k);
                fx(p, GunFxPacket.LOADED, FirearmItem.ammo(stack));
            }
            return;
        }
        if (s.cooldown > 0) s.cooldown--;
        if (k.boltAction() && s.cooldown == 21) sound(p, "bolt_cycle", 0.8f, 1.0f);   // T-5000: bolt cycled after the shot
        if (!s.trigger) {
            s.credit = 0;
            return;
        }
        int ammo = FirearmItem.ammo(stack);
        if (ammo <= 0) {
            if (!s.dryDone) {
                sound(p, "dry_fire", 0.7f, 1.0f);
                fx(p, GunFxPacket.DRY, 0);
                s.dryDone = true;
            }
            s.credit = 0;
            return;
        }
        boolean auto = k.auto && (!k.selector() || FirearmItem.mode(stack) == 1);
        if (!auto) {
            if (!s.semiDone && s.cooldown == 0) {
                fire(p, stack, k, s.aiming);
                s.semiDone = true;
                s.cooldown = k.launcher() ? 10 : k.boltAction() ? 26 : 2;
            }
            return;
        }
        s.credit += k.perTick();
        while (s.credit >= 1f && FirearmItem.ammo(stack) > 0) {
            s.credit -= 1f;
            fire(p, stack, k, s.aiming);
        }
    }

    @SubscribeEvent
    public static void logout(PlayerEvent.PlayerLoggedOutEvent e) {
        STATES.remove(e.getEntity().getUUID());
    }

    // ------------------------------------------------------------------ firing

    /** One round (public for gametests: works with fake players). */
    public static void fire(Player p, ItemStack stack, GunKind k, boolean aiming) {
        if (!(p.level() instanceof ServerLevel sl)) return;
        int ammo = FirearmItem.ammo(stack);
        if (ammo <= 0) return;
        FirearmItem.setAmmo(stack, ammo - 1);
        Vec3 look = p.getLookAngle();
        double moving = p.getDeltaMovement().horizontalDistance() > 0.08 ? 2.2 : 1.0;
        double spread = (aiming ? k.adsSpread : k.hipSpread) * moving * (p.isCrouching() ? 0.7 : 1.0);
        Vec3 dir = jitter(look, spread, sl);
        if (k.launcher()) {
            Vec3 right = look.cross(new Vec3(0, 1, 0)).normalize();
            Vec3 pos = p.getEyePosition().add(look.scale(1.0)).add(right.scale(aiming ? 0.05 : 0.22)).add(0, -0.08, 0);
            AtMissileEntity.launch(sl, p, HandheldKind.RPG7, pos, dir, -1, null);
            sl.playSound(null, p.getX(), p.getY(), p.getZ(), ru.aiforge.realwar.registry.ModSounds.ROCKET_LAUNCH_SMALL.get(), SoundSource.PLAYERS, 2.4f, 1.0f);
            backblast(sl, p, look);
        } else {
            Bullet b = new Bullet();
            b.pos = p.getEyePosition();
            b.origin = b.pos;
            b.vel = dir.scale(k.speed / 20.0);
            b.owner = p.getId();
            b.dmg = k.damage;
            b.pen = k.pen;
            List<Bullet> l = BULLETS.computeIfAbsent(sl, x -> new ArrayList<>());
            if (l.size() < 4000) l.add(b);
            sound(p, k.sound, 3.0f, 0.95f + sl.random.nextFloat() * 0.1f);
            Vec3 m = p.getEyePosition().add(look.scale(0.9)).add(0, -0.1, 0);
            sl.sendParticles(ParticleTypes.SMOKE, m.x, m.y, m.z, 1, 0.02, 0.02, 0.02, 0.005);
        }
        fx(p, GunFxPacket.SHOT, FirearmItem.ammo(stack));
    }

    private static Vec3 jitter(Vec3 d, double cone, ServerLevel sl) {
        if (cone <= 0) return d;
        double a = sl.random.nextDouble() * Math.PI * 2, r = Math.sqrt(sl.random.nextDouble()) * cone;
        Vec3 up = Math.abs(d.y) > 0.95 ? new Vec3(1, 0, 0) : new Vec3(0, 1, 0);
        Vec3 u = d.cross(up).normalize(), v = u.cross(d).normalize();
        return d.add(u.scale(Math.cos(a) * r)).add(v.scale(Math.sin(a) * r)).normalize();
    }

    /** RPG-7: ~6 m dangerous cone behind the venturi (burns). */
    static void backblast(ServerLevel sl, Player p, Vec3 look) {
        double len = 6.0;
        Vec3 back = p.getEyePosition().subtract(look.scale(0.5));
        for (int i = 0; i < 16; i++) {
            double f = 0.4 + i / 16.0 * len;
            Vec3 q = back.subtract(look.scale(f));
            sl.sendParticles(i < 4 ? ParticleTypes.FLAME : ParticleTypes.CAMPFIRE_COSY_SMOKE, q.x, q.y, q.z, 1,
                    0.18 * f / len, 0.18 * f / len, 0.18 * f / len, 0.01);
        }
        for (Entity e : sl.getEntities(p, new AABB(back, back).inflate(len))) {
            if (!(e instanceof LivingEntity le)) continue;
            Vec3 to = e.getBoundingBox().getCenter().subtract(back);
            double d = to.length();
            if (d > len || d < 1e-3 || to.scale(1 / d).dot(look.reverse()) < 0.75) continue;
            le.hurt(sl.damageSources().inFire(), (float) (6.0 * (1 - d / len) + 1));
            le.setSecondsOnFire(2);
        }
    }

    // ------------------------------------------------------------------ bullets

    public static int bullets(ServerLevel sl) {
        List<Bullet> l = BULLETS.get(sl);
        return l == null ? 0 : l.size();
    }

    @SubscribeEvent
    public static void levelTick(TickEvent.LevelTickEvent e) {
        if (e.phase != TickEvent.Phase.END || !(e.level instanceof ServerLevel sl)) return;
        List<Bullet> l = BULLETS.get(sl);
        if (l == null || l.isEmpty()) return;
        Iterator<Bullet> it = l.iterator();
        while (it.hasNext()) {
            if (!step(sl, it.next())) it.remove();
        }
    }

    @SubscribeEvent
    public static void unload(LevelEvent.Unload e) {
        if (e.getLevel() instanceof ServerLevel sl) BULLETS.remove(sl);
    }

    private static boolean step(ServerLevel sl, Bullet b) {
        Vec3 from = b.pos;
        Vec3 to = from.add(b.vel);
        if (!sl.hasChunkAt(BlockPos.containing(to))) return false;
        double bestD = Double.MAX_VALUE;
        Vec3 hitPos = null;
        Entity hit = null;
        BlockHitResult bh = sl.clip(new ClipContext(from, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, null));
        if (bh.getType() != HitResult.Type.MISS) {
            bestD = bh.getLocation().distanceToSqr(from);
            hitPos = bh.getLocation();
        }
        AABB box = new AABB(from, to).inflate(0.5);
        for (Entity e : sl.getEntities((Entity) null, box.inflate(20.0), x -> x instanceof ru.aiforge.realwar.vehicle.VehicleEntity && x.isAlive())) {
            if (e.getId() == b.owner) continue;
            Vec3 c = ru.aiforge.realwar.damage.VehicleHit.clip((ru.aiforge.realwar.vehicle.VehicleEntity) e, from, to);
            if (c == null) continue;
            double d = c.distanceToSqr(from);
            if (d < bestD) {
                bestD = d;
                hit = e;
                hitPos = c;
            }
        }
        for (Entity e : sl.getEntities((Entity) null, box, x -> !(x instanceof ru.aiforge.realwar.vehicle.VehicleEntity) && x.isAlive() && !x.isSpectator()
                && (x instanceof LivingEntity || x.isPickable()))) {
            if (e.getId() == b.owner || e.getVehicle() != null && e.getVehicle().getId() == b.owner) continue;
            var c = e.getBoundingBox().inflate(0.1).clip(from, to);
            if (c.isEmpty()) continue;
            double d = c.get().distanceToSqr(from);
            if (d < bestD) {
                bestD = d;
                hit = e;
                hitPos = c.get();
            }
        }
        if (hitPos != null) {
            Vec3 dir = b.vel.normalize();
            if (hit != null) {
                double v = b.vel.length() * 20.0;
                float dmg = b.dmg * (float) Math.max(0.45, Math.min(1.0, v * v / (900.0 * 900.0) * 1.15));
                if (hit instanceof LivingEntity le && !(hit instanceof ru.aiforge.realwar.vehicle.VehicleEntity)
                        && hitPos.y > le.getEyeY() - 0.22 && le.getBbHeight() > 1.0f) dmg *= 2.0f;     // head
                Entity owner = sl.getEntity(b.owner);
                DamageSource src = owner != null
                        ? new DamageSource(sl.registryAccess().registryOrThrow(Registries.DAMAGE_TYPE).getHolderOrThrow(ModDamage.BULLET), owner)
                        : ModDamage.source(sl, ModDamage.BULLET);
                hit.invulnerableTime = 0;
                HitContext.hurt(hit, src, dmg, hitPos, dir, HitContext.Kind.BULLET, b.pen);
                hit.invulnerableTime = 0;
                sl.sendParticles(ParticleTypes.CRIT, hitPos.x, hitPos.y, hitPos.z, 3, 0.08, 0.08, 0.08, 0.15);
            } else {
                BlockState bs = sl.getBlockState(bh.getBlockPos());
                if (!bs.isAir()) {
                    sl.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, bs), hitPos.x, hitPos.y, hitPos.z, 5, 0.04, 0.04, 0.04, 0.08);
                }
                sl.sendParticles(ParticleTypes.SMOKE, hitPos.x, hitPos.y, hitPos.z, 1, 0.03, 0.03, 0.03, 0.01);
                if (bs.getSoundType() != null && sl.random.nextInt(2) == 0) {
                    sl.playSound(null, hitPos.x, hitPos.y, hitPos.z, bs.getSoundType().getHitSound(), SoundSource.BLOCKS, 0.5f, 1.4f);
                }
            }
            return false;
        }
        b.pos = to;
        b.vel = new Vec3(b.vel.x * DRAG, b.vel.y * DRAG - G, b.vel.z * DRAG);
        return ++b.age < LIFE;
    }

    // ------------------------------------------------------------------ helpers

    private static void sound(Player p, String name, float vol, float pitch) {
        SoundEvent ev = ForgeRegistries.SOUND_EVENTS.getValue(new net.minecraft.resources.ResourceLocation("aiarsenal", name));
        if (ev != null) p.level().playSound(null, p.getX(), p.getEyeY(), p.getZ(), ev, SoundSource.PLAYERS, vol, pitch);
    }

    private static void fx(Player p, int fx, int ammo) {
        if (p instanceof ServerPlayer sp && !(p instanceof net.minecraftforge.common.util.FakePlayer)) {
            ModNetwork.sendToPlayer(sp, new GunFxPacket(fx, ammo));
        }
    }
}
