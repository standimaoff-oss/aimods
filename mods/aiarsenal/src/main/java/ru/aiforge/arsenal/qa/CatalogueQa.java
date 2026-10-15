package ru.aiforge.arsenal.qa;

import com.google.gson.*;
import com.mojang.brigadier.arguments.StringArgumentType;
import java.nio.file.*;
import net.minecraft.commands.Commands;
import net.minecraft.core.*;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.*;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.*;
import net.minecraft.world.entity.animal.Pig;
import net.minecraft.world.item.*;
import net.minecraft.world.phys.*;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import ru.aiforge.realwar.handheld.*;
import ru.aiforge.realwar.blast.BlastManager;

/** Destructive diagnostics ONLY on an explicitly opted-in disposable server.
 * Never registered in normal games. Uses live registry entries and production item/
 * bomb paths; does not substitute visual-only explosion packets for detonations. */
@Mod.EventBusSubscriber(modid="aiarsenal")
public final class CatalogueQa {
    private static Entity bomb;
    private static Pig witness;
    private static long blocksBefore;
    private CatalogueQa() {}

    @SubscribeEvent public static void register(RegisterCommandsEvent event) {
        if (!Boolean.getBoolean("aiarsenal.stressQa")) return;
        var root = Commands.literal("arsenal_stress").requires(s -> s.hasPermission(2));
        root.then(Commands.literal("catalogue").executes(c -> {
            JsonArray items = new JsonArray();
            for (var id : BuiltInRegistries.ITEM.keySet().stream().filter(i -> i.getNamespace().equals("aiarsenal")).sorted().toList()) {
                Item item = BuiltInRegistries.ITEM.get(id);
                JsonObject row = new JsonObject();
                row.addProperty("id", id.toString()); row.addProperty("class", item.getClass().getName());
                row.addProperty("armor", item instanceof ArmorItem); row.addProperty("block", item instanceof BlockItem);
                if (item instanceof FirearmItem gun) {
                    var k = gun.kind;
                    row.addProperty("ammo", "aiarsenal:" + k.ammo); row.addProperty("capacity", k.cap);
                    row.addProperty("reloadTicks", k.reloadEmpty); row.addProperty("incremental", k.incrementalReload());
                    row.addProperty("manpads", k.manpads());
                }
                ItemStack stack = new ItemStack(item);
                stack.getOrCreateTag().putString("CatalogueQa", id.toString());
                row.addProperty("nbtRoundtrip", ItemStack.isSameItemSameTags(stack, ItemStack.of(stack.save(new CompoundTag()))));
                items.add(row);
            }
            JsonArray bombs = new JsonArray();
            for (var t : ru.aiforge.realwar.aircraft.AirBombType.values()) bombs.add("air:" + t.name());
            for (var t : ru.aiforge.tubombers.aircraft.BombType.values()) if (t.arsenal() == null) bombs.add("tu:" + t.name());
            for (var t : ru.aiforge.realwar.registry.BombType.values()) bombs.add("rw:" + t.name());
            for (var t : ru.aiforge.arsenal.core.Kind.values()) if (t.cat == ru.aiforge.arsenal.core.Kind.Cat.NUKE) bombs.add("ars:" + t.name());
            JsonObject out = new JsonObject(); out.add("items", items); out.add("freeFallBombs", bombs);
            try {
                Files.createDirectories(Path.of("logs"));
                Files.writeString(Path.of("logs/arsenal-catalogue.json"), new GsonBuilder().setPrettyPrinting().create().toJson(out));
            } catch (java.io.IOException ex) { throw new IllegalStateException(ex); }
            c.getSource().sendSuccess(() -> Component.literal("CATALOGUE items=" + items.size() + " freeFallBombs=" + bombs.size()), false);
            return items.size();
        }));
        root.then(Commands.literal("use").executes(c -> {
            ServerPlayer p = c.getSource().getPlayerOrException();
            ItemStack stack = p.getMainHandItem();
            // Live ServerPlayer, network and inventory, not a FakePlayer. Generic smoke
            // coverage only: PASS/FAIL here is an interaction result, not proof of a feature.
            var air = p.gameMode.useItem(p, p.level(), stack, InteractionHand.MAIN_HAND);
            BlockPos at = p.blockPosition().offset(0,-1,2);
            var block = p.gameMode.useItemOn(p, p.serverLevel(), p.getMainHandItem(), InteractionHand.MAIN_HAND,
                    new BlockHitResult(Vec3.atCenterOf(at).add(0,.5,0), Direction.UP, at, false));
            c.getSource().sendSuccess(() -> Component.literal("USE air=" + air + " block=" + block + " using=" + p.isUsingItem()), false);
            return 1;
        }));
        root.then(Commands.literal("drop").then(Commands.argument("type", StringArgumentType.greedyString()).executes(c -> {
            var level = c.getSource().getLevel();
            if (BlastManager.active(level) != 0 || ru.aiforge.arsenal.nuke.NuclearBlast.busy()) throw new IllegalStateException("previous blast still active");
            Vec3 at = c.getSource().getPosition().add(0,45,25);
            String[] key = StringArgumentType.getString(c,"type").split(":");
            Entity next = switch(key[0]) {
                case "air" -> ru.aiforge.realwar.aircraft.AirBombEntity.drop(level, at, Vec3.ZERO,
                        ru.aiforge.realwar.aircraft.AirBombType.valueOf(key[1]));
                case "rw" -> ru.aiforge.realwar.entity.FallingBombEntity.drop(level, at, Vec3.ZERO,
                        ru.aiforge.realwar.registry.BombType.valueOf(key[1]), Direction.NORTH);
                case "tu" -> {
                    var owner = ru.aiforge.tubombers.registry.ModRegistry.TU95.get().create(level);
                    yield ru.aiforge.tubombers.entity.BombEntity.create(level, ru.aiforge.tubombers.aircraft.BombType.valueOf(key[1]),
                            new org.joml.Vector3d(at.x,at.y,at.z), new org.joml.Vector3d(), owner);
                }
                case "ars" -> ru.aiforge.arsenal.entity.NukeEntity.create(level, ru.aiforge.arsenal.core.Kind.valueOf(key[1]),
                        at, Vec3.ZERO, 0, ru.aiforge.arsenal.nuke.ChargeRegistry.FUZE_CONTACT, null, true);
                default -> throw new IllegalArgumentException("unknown bomb family");
            };
            if (!key[0].equals("ars") && !level.addFreshEntity(next)) throw new IllegalStateException("bomb spawn refused");
            bomb = next; blocksBefore = BlastManager.totalBlocksChanged;
            if (witness != null) witness.discard();
            witness = EntityType.PIG.create(level);
            witness.setNoAi(true); witness.setPersistenceRequired();
            witness.setPos(at.x + 3, at.y - 45, at.z);
            level.addFreshEntity(witness);
            c.getSource().sendSuccess(() -> Component.literal("DROPPED " + key[0] + ":" + key[1] + " uuid=" + next.getUUID()), false);
            return 1;
        })));
        root.then(Commands.literal("bombstatus").executes(c -> {
            JsonObject o = new JsonObject();
            o.addProperty("removed", bomb != null && bomb.isRemoved());
            o.addProperty("removalReason", bomb == null || bomb.getRemovalReason() == null ? "none" : bomb.getRemovalReason().name());
            o.addProperty("witnessHealth", witness == null ? -1 : witness.getHealth());
            o.addProperty("witnessDead", witness != null && witness.isDeadOrDying());
            o.addProperty("activeBlasts", BlastManager.active(c.getSource().getLevel()));
            o.addProperty("legacyBusy", ru.aiforge.arsenal.nuke.NuclearBlast.busy());
            o.addProperty("changedBlocks", BlastManager.totalBlocksChanged - blocksBefore);
            c.getSource().sendSuccess(() -> Component.literal(o.toString()), false);
            return 1;
        }));
        event.getDispatcher().register(root);
    }
}
