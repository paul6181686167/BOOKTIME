package com.booktime.app;

import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.view.Window;
import android.view.WindowManager;
import androidx.core.view.WindowCompat;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(SystemBarsPlugin.class);
        super.onCreate(savedInstanceState);

        Window window = getWindow();
        window.clearFlags(WindowManager.LayoutParams.FLAG_TRANSLUCENT_NAVIGATION);
        window.addFlags(WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS);
        // Layout classique : le WebView scrolle normalement ; la couleur nav est
        // appliquée en opaque via SystemBarsPlugin (pas de transparent vert mist).
        WindowCompat.setDecorFitsSystemWindows(window, true);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            window.setNavigationBarContrastEnforced(false);
        }
        // Défaut avant le 1er appel JS — sera remplacé par le thème
        window.setNavigationBarColor(Color.parseColor("#050505"));
    }
}
