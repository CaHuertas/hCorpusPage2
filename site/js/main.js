(function () {
  "use strict";

  var header = document.getElementById("siteHeader");
  var navToggle = document.getElementById("navToggle");
  var mobileNav = document.getElementById("mobileNav");
  var yearEl = document.getElementById("year");
  var form = document.getElementById("contactForm");
  var formStatus = document.getElementById("formStatus");

  if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
  }

  // Header: sombra al hacer scroll
  function onScroll() {
    if (window.scrollY > 8) {
      header.classList.add("is-scrolled");
    } else {
      header.classList.remove("is-scrolled");
    }
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // Menú móvil
  function syncHeaderHeight() {
    if (header) {
      document.documentElement.style.setProperty("--header-h", header.offsetHeight + "px");
    }
  }
  syncHeaderHeight();
  window.addEventListener("resize", syncHeaderHeight);

  function closeMobileNav() {
    mobileNav.classList.remove("is-open");
    navToggle.setAttribute("aria-expanded", "false");
    navToggle.setAttribute("aria-label", "Abrir menú de navegación");
  }

  function openMobileNav() {
    syncHeaderHeight();
    mobileNav.classList.add("is-open");
    navToggle.setAttribute("aria-expanded", "true");
    navToggle.setAttribute("aria-label", "Cerrar menú de navegación");
  }

  if (navToggle && mobileNav) {
    navToggle.addEventListener("click", function () {
      var isOpen = navToggle.getAttribute("aria-expanded") === "true";
      if (isOpen) {
        closeMobileNav();
      } else {
        openMobileNav();
      }
    });

    mobileNav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", closeMobileNav);
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && navToggle.getAttribute("aria-expanded") === "true") {
        closeMobileNav();
        navToggle.focus();
      }
    });

    window.addEventListener("resize", function () {
      if (window.innerWidth >= 1024) {
        closeMobileNav();
      }
    });
  }

  // Dropdown "Servicios" (escritorio)
  var dropdownToggles = document.querySelectorAll(".nav-dropdown-toggle");

  function closeAllDropdowns() {
    dropdownToggles.forEach(function (t) {
      var p = document.getElementById(t.getAttribute("aria-controls"));
      if (p) p.classList.remove("is-open");
      t.setAttribute("aria-expanded", "false");
    });
  }

  dropdownToggles.forEach(function (toggle) {
    var panel = document.getElementById(toggle.getAttribute("aria-controls"));
    if (!panel) return;

    toggle.addEventListener("click", function (e) {
      e.stopPropagation();
      var isOpen = toggle.getAttribute("aria-expanded") === "true";
      closeAllDropdowns();
      if (!isOpen) {
        panel.classList.add("is-open");
        toggle.setAttribute("aria-expanded", "true");
      }
    });
  });

  if (dropdownToggles.length) {
    document.addEventListener("click", function (e) {
      if (!e.target.closest(".has-dropdown")) {
        closeAllDropdowns();
      }
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeAllDropdowns();
    });
  }

  // Acordeón de submenú (móvil)
  var subnavToggles = document.querySelectorAll(".mobile-subnav-toggle");
  subnavToggles.forEach(function (btn) {
    var panel = document.getElementById(btn.getAttribute("aria-controls"));
    if (!panel) return;
    btn.addEventListener("click", function () {
      var isOpen = btn.getAttribute("aria-expanded") === "true";
      btn.setAttribute("aria-expanded", isOpen ? "false" : "true");
      panel.classList.toggle("is-open", !isOpen);
    });
  });

  // Reveal on scroll
  var revealItems = document.querySelectorAll("[data-reveal]");
  var prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (revealItems.length && !prefersReducedMotion && "IntersectionObserver" in window) {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
    );
    revealItems.forEach(function (item) {
      observer.observe(item);
    });
  } else {
    revealItems.forEach(function (item) {
      item.classList.add("is-visible");
    });
  }

  // Formulario de contacto -> mailto
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();

      var nombre = form.nombre.value.trim();
      var correo = form.correo.value.trim();
      var organizacion = form.organizacion.value.trim();
      var mensaje = form.mensaje.value.trim();
      var autorizacion = form.autorizacion.checked;

      if (!nombre || !correo || !mensaje) {
        formStatus.textContent = "Por favor completa los campos obligatorios.";
        formStatus.className = "form-status is-visible err";
        return;
      }

      if (!autorizacion) {
        formStatus.textContent = "Debes autorizar el tratamiento de tus datos personales para continuar.";
        formStatus.className = "form-status is-visible err";
        return;
      }

      var subject = encodeURIComponent("Contacto desde hcorpus.co — " + nombre);
      var bodyLines = [
        "Nombre: " + nombre,
        "Correo: " + correo,
        "Organización: " + (organizacion || "—"),
        "",
        mensaje
      ];
      var body = encodeURIComponent(bodyLines.join("\n"));

      window.location.href = "mailto:gerencia@h-corpus.com?subject=" + subject + "&body=" + body;

      formStatus.textContent = "Se abrió tu cliente de correo con el mensaje listo para enviar.";
      formStatus.className = "form-status is-visible ok";
    });
  }
})();
