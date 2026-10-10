package ru.aiforge.realwar.grenade;

import net.minecraft.sounds.SoundSource;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import ru.aiforge.realwar.item.TooltipItem;
import ru.aiforge.realwar.registry.ModSounds;

/**
 * r27: hand grenade. Right click pulls the pin and throws it (the fuse runs on the {@link GrenadeEntity}).
 * Creative players keep the stack.
 */
public class GrenadeItem extends TooltipItem {
    public final GrenadeKind kind;

    public GrenadeItem(GrenadeKind kind, Item.Properties p) {
        super(p.stacksTo(16));
        this.kind = kind;
    }

    public static GrenadeKind kindOf(ItemStack s) {
        return s.getItem() instanceof GrenadeItem g ? g.kind : GrenadeKind.RGD5;
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player p, InteractionHand hand) {
        ItemStack held = p.getItemInHand(hand);
        if (p.getCooldowns().isOnCooldown(this)) {
            return InteractionResultHolder.fail(held);
        }
        if (!level.isClientSide && level instanceof ServerLevel sl) {
            GrenadeEntity g = new GrenadeEntity(sl, p, held.copyWithCount(1));
            g.shootFromRotation(p, p.getXRot(), p.getYRot(), -12.0f, 0.95f, 1.0f);
            sl.addFreshEntity(g);
            sl.playSound(null, p.getX(), p.getY(), p.getZ(), ModSounds.GRENADE_PIN.get(), SoundSource.PLAYERS, 0.8f, 1.0f);
            sl.playSound(null, p.getX(), p.getY(), p.getZ(), ModSounds.GRENADE_THROW.get(), SoundSource.PLAYERS, 0.7f, 1.0f);
            if (!p.getAbilities().instabuild) {
                held.shrink(1);
            }
        }
        p.getCooldowns().addCooldown(this, 20);
        return InteractionResultHolder.sidedSuccess(held, level.isClientSide);
    }
}
