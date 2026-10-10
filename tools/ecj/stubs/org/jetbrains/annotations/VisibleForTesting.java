package org.jetbrains.annotations;
public @interface VisibleForTesting { String value() default ""; String pure() default ""; }
