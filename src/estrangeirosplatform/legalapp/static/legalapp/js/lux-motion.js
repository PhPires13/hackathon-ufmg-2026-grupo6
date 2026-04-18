(function () {
    "use strict";

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        return;
    }

    var layouts = document.querySelectorAll(".layout");
    if (!layouts.length) {
        return;
    }

    layouts.forEach(function (layout, layoutIndex) {
        if (layout.querySelector(".bg-particles")) {
            return;
        }

        var particleLayer = document.createElement("div");
        particleLayer.className = "bg-particles";

        var particlesCount = 18;
        for (var i = 0; i < particlesCount; i += 1) {
            var particle = document.createElement("span");
            particle.className = "bg-particle";

            var size = 4 + Math.random() * 8;
            var x = Math.random() * 100;
            var y = Math.random() * 100;
            var opacity = 0.12 + Math.random() * 0.26;
            var duration = 10 + Math.random() * 12;
            var delay = -Math.random() * 16;
            var travelX = -24 + Math.random() * 48;
            var travelY = -(18 + Math.random() * 36);

            particle.style.setProperty("--size", size.toFixed(2) + "px");
            particle.style.setProperty("--x", x.toFixed(2) + "%");
            particle.style.setProperty("--y", y.toFixed(2) + "%");
            particle.style.setProperty("--opacity", opacity.toFixed(2));
            particle.style.setProperty("--dur", duration.toFixed(2) + "s");
            particle.style.setProperty("--delay", delay.toFixed(2) + "s");
            particle.style.setProperty("--travel-x", travelX.toFixed(2) + "px");
            particle.style.setProperty("--travel-y", travelY.toFixed(2) + "px");

            particleLayer.appendChild(particle);
        }

        layout.appendChild(particleLayer);

        var ticking = false;
        function applyParallax() {
            var rect = layout.getBoundingClientRect();
            var scrollDepth = Math.max(0, -rect.top) + window.scrollY * 0.06;
            layout.style.setProperty("--parallax-y", (scrollDepth * 0.12).toFixed(2) + "px");
            ticking = false;
        }

        function requestParallax() {
            if (ticking) {
                return;
            }
            ticking = true;
            window.requestAnimationFrame(applyParallax);
        }

        window.addEventListener("scroll", requestParallax, { passive: true });
        window.addEventListener("resize", requestParallax);

        if (layoutIndex === 0) {
            requestParallax();
        }
    });
})();
