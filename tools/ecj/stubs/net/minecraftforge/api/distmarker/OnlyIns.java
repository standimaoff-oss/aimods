package net.minecraftforge.api.distmarker;
import java.lang.annotation.*;
@Retention(RetentionPolicy.CLASS) @Target({ElementType.TYPE})
public @interface OnlyIns { OnlyIn[] value(); }
