package org.jetbrains.annotations;
public @interface UnmodifiableView { String value() default ""; String pure() default ""; }
