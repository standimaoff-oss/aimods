package org.jetbrains.annotations;
public @interface Unmodifiable { String value() default ""; String pure() default ""; }
