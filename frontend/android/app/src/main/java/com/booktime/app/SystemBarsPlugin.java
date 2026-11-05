package com.booktime.app;

import android.graphics.Color;
import android.os.Build;
import android.view.View;
import android.view.Window;
import androidx.core.view.WindowCompat;
import androidx.core.view.WindowInsetsControllerCompat;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

/**
 * Couleur de la barre de navigation système Android (retour / accueil),
 * distincte de la barre d’onglets Booktime.
 */
@CapacitorPlugin(name = "SystemBars")
public class SystemBarsPlugin extends Plugin {

    @PluginMethod
    public void setNavigationBarColor(PluginCall call) {
        String color = call.getString("color");
        if (color == null || color.isEmpty()) {
            call.reject("color requis");
            return;
        }
        boolean darkButtons = Boolean.TRUE.equals(call.getBoolean("darkButtons", true));

        getActivity().runOnUiThread(() -> {
            try {
                Window window = getActivity().getWindow();
                int parsed = Color.parseColor(color);
                window.setNavigationBarColor(parsed);

                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                    window.setNavigationBarContrastEnforced(false);
                }

                View decor = window.getDecorView();
                WindowInsetsControllerCompat controller =
                    WindowCompat.getInsetsController(window, decor);
                if (controller != null) {
                    controller.setAppearanceLightNavigationBars(darkButtons);
                }
                call.resolve();
            } catch (Exception e) {
                call.reject("Impossible de colorer la barre système", e);
            }
        });
    }
}
