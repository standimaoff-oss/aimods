package ru.aiforge.realwar.client.render;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.inventory.CreativeModeInventoryScreen;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.CreativeModeTab;
import ru.aiforge.arsenal.AiArsenal;
import ru.aiforge.realwar.registry.ModTabs;

/** Fixed, opt-in CI checks, never active for an ordinary player. No arbitrary code/file/network input. */
public final class WeaponViewQa {
    private WeaponViewQa() {}
    public static String run(String action) {
        if (!Boolean.getBoolean("aiarsenal.visualQa")) return "disabled";
        Minecraft mc = Minecraft.getInstance();
        switch (action) {
            case "view_shaderfail" -> ru.aiforge.arsenal.volumetric.client.render.VolumeGlRenderer.failNextShaderForQa();
            case "view_fov90" -> mc.options.fov().set(90);
            case "view_fov70" -> mc.options.fov().set(70);
            case "view_scale3" -> { mc.options.guiScale().set(3); mc.resizeDisplay(); }
            case "view_scale2" -> { mc.options.guiScale().set(2); mc.resizeDisplay(); }
            case "view_reload" -> mc.reloadResourcePacks().thenRun(() -> mc.execute(() ->
                    AiArsenal.LOGGER.info("VIEW RELOAD PASS")));
            case "view_tabs", "view_modern" -> {
                var screen = new CreativeModeInventoryScreen(mc.player, mc.player.connection.enabledFeatures(),
                        mc.options.operatorItemsTab().get());
                mc.setScreen(screen);
                String section = action.equals("view_tabs") ? "ww2_weapons" : "modern_vehicles";
                CreativeModeTab tab = BuiltInRegistries.CREATIVE_MODE_TAB.get(new ResourceLocation("aiarsenal", section));
                // selectTab is private in vanilla; discover by its sole CreativeModeTab parameter, not an obfuscated name.
                try {
                    var methods = java.util.Arrays.stream(CreativeModeInventoryScreen.class.getDeclaredMethods())
                            .filter(m -> m.getParameterCount() == 1 && m.getParameterTypes()[0] == CreativeModeTab.class
                                    && m.getReturnType() == void.class).toList();
                    if (methods.size() != 1) throw new IllegalStateException("ambiguous selectTab: " + methods);
                    methods.get(0).setAccessible(true);
                    methods.get(0).invoke(screen, tab);
                } catch (ReflectiveOperationException ex) { throw new IllegalStateException(ex); }
                for (var id : ModTabs.SECTIONS) AiArsenal.LOGGER.info("VIEW TAB {} items={}", id, ModTabs.content(id).size());
            }
            default -> throw new IllegalArgumentException(action);
        }
        String result = "VIEW QA " + action + " PASS";
        AiArsenal.LOGGER.info(result);
        return result;
    }
}
