package org.jetbrains.annotations;
public final class ApiStatus { public @interface Internal {} public @interface Experimental {} public @interface OverrideOnly {} public @interface NonExtendable {} public @interface ScheduledForRemoval { String inVersion() default ""; } public @interface AvailableSince { String value(); } public @interface Obsolete { String since() default ""; } }
