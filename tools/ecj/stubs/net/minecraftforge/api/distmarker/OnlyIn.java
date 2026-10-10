package net.minecraftforge.api.distmarker;
import java.lang.annotation.*;
@Retention(RetentionPolicy.CLASS) @Target({ElementType.TYPE, ElementType.FIELD, ElementType.METHOD, ElementType.CONSTRUCTOR, ElementType.PACKAGE})
@Repeatable(OnlyIns.class)
public @interface OnlyIn { Dist value(); Class<?> _interface() default Object.class; }
