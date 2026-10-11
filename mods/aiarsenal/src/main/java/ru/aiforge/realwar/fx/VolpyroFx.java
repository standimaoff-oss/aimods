package ru.aiforge.realwar.fx;

import java.lang.reflect.Field;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.fml.ModList;
import net.minecraftforge.network.PacketDistributor;
import net.minecraftforge.network.simple.SimpleChannel;

/**
 * Мост к объёмным взрывам мода VolPyro (volpyro 1.5.6, MIT).
 *
 * Если VolPyro загружен, взрывы мода показываются его объёмными эффектами вместо собственных
 * пакетов aiarsenal. Без VolPyro вызывающий код использует старые эффекты (см. {@link #available()}).
 *
 * Классы VolPyro не загружаются, пока {@link #available()} не вернёт true: пакеты создаются
 * через Object и рефлексию, а канал VolPyro (ModNetwork.CHANNEL, не public) тоже берётся рефлексией.
 */
public final class VolpyroFx {
    private static final String MODID = "volpyro";
    private static Boolean loaded;
    private static SimpleChannel channel;

    private VolpyroFx() {
    }

    public static boolean available() {
        if (loaded == null) {
            ModList list = ModList.get();
            loaded = list != null && list.isLoaded(MODID);
        }
        return loaded;
    }

    /** Обычный (ВВ / фугас) взрыв. Сила ≈ радиус визуала, растёт с корнем кубическим из массы. */
    public static void conventional(ServerLevel level, Vec3 pos, double massKg) {
        float yield = (float) Math.min(40.0, 4.0 + 1.6 * Math.cbrt(massKg));
        try {
            Object msg = newInstance("com.example.volpyro.network.Messages$S2CSpawnExplosion",
                    new Class<?>[]{double.class, double.class, double.class, float.class, long.class},
                    pos.x, pos.y, pos.z, yield, level.random.nextLong());
            send(level, pos, msg);
        } catch (ReflectiveOperationException e) {
            loaded = Boolean.FALSE; // VolPyro без ожидаемых классов: дальше только старые эффекты
        }
    }

    /** Ядерный взрыв. Вариант VolPyro выбирается по мощности: NUKE / RDS4 / TSAR_BOMBA. */
    public static void nuke(ServerLevel level, Vec3 burst, double yieldKt, float radius, double surfaceY) {
        int variant = yieldKt >= 3000.0 ? 2 : yieldKt >= 200.0 ? 1 : 0;
        try {
            Object msg = newInstance("com.example.volpyro.network.NukeMessages$S2CSpawnNuke",
                    new Class<?>[]{double.class, double.class, double.class, int.class, float.class,
                            long.class, boolean.class, double.class},
                    burst.x, burst.y, burst.z, variant, radius, level.random.nextLong(), false, surfaceY);
            send(level, burst, msg);
        } catch (ReflectiveOperationException e) {
            loaded = Boolean.FALSE;
        }
    }

    private static Object newInstance(String cls, Class<?>[] types, Object... args) throws ReflectiveOperationException {
        return Class.forName(cls).getConstructor(types).newInstance(args);
    }

    private static void send(ServerLevel level, Vec3 pos, Object msg) throws ReflectiveOperationException {
        if (channel == null) {
            Field f = Class.forName("com.example.volpyro.network.ModNetwork").getDeclaredField("CHANNEL");
            f.setAccessible(true);
            channel = (SimpleChannel) f.get(null);
        }
        channel.send(PacketDistributor.TRACKING_CHUNK.with(() -> level.getChunkAt(BlockPos.containing(pos))), msg);
    }
}
