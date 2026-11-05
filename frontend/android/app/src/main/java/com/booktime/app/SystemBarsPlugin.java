package com.booktime.app;

import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.os.Build;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import androidx.core.view.WindowCompat;
import androidx.core.view.WindowInsetsControllerCompat;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

/**
 * Couleur opaque de la barre de navigation système (= fond de l’app).
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
        Boolean darkButtonsArg = call.getBoolean("darkButtons", true);
        boolean darkButtons = darkButtonsArg == null || darkButtonsArg;

        getActivity().runOnUiThread(() -> {
            try {
                Window window = getActivity().getWindow();
                int parsed = Color.parseColor(color);

                window.clearFlags(WindowManager.LayoutParams.FLAG_TRANSLUCENT_NAVIGATION);
                window.clearFlags(WindowManager.LayoutParams.FLAG_TRANSLUCENT_STATUS);
                window.addFlags(WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS);

                // Pas d’edge-to-edge : barre opaque = couleur du thème (évite le vert mist)
                WindowCompat.setDecorFitsSystemWindows(window, true);
                window.setNavigationBarColor(parsed);
                window.setStatusBarColor(parsed);
                window.setBackgroundDrawable(new ColorDrawable(parsed));

                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                    window.setNavigationBarContrastEnforced(false);
                }

                View decor = window.getDecorView();
                WindowInsetsControllerCompat controller =
                    WindowCompat.getInsetsController(window, decor);
                if (controller != null) {
                    controller.setAppearanceLightNavigationBars(darkButtons);
                    controller.setAppearanceLightStatusBars(darkButtons);
                }
                call.resolve();
            } catch (Exception e) {
                call.reject("Impossible de colorer la barre système", e);
            }
        });
    }
}
