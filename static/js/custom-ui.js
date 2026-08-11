/* ==========================================================================
   Modern Custom UI Script for Django E-Commerce
   ========================================================================== */

document.addEventListener("DOMContentLoaded", function () {
  // 1. Sticky Header Scroll Effect
  const header = document.querySelector(".header");
  if (header) {
    window.addEventListener("scroll", function () {
      if (window.scrollY > 40) {
        header.classList.add("scrolled");
      } else {
        header.classList.remove("scrolled");
      }
    });
  }

  // 2. Mini Cart Drawer Toggle
  const cartDrawer = document.getElementById("cartDrawer");
  const cartDrawerOverlay = document.getElementById("cartDrawerOverlay");
  const cartDrawerClose = document.getElementById("cartDrawerClose");

  function openCartDrawer() {
    if (cartDrawer && cartDrawerOverlay) {
      cartDrawer.classList.add("active");
      cartDrawerOverlay.classList.add("active");
      document.body.style.overflow = "hidden";
    }
  }

  function closeCartDrawer() {
    if (cartDrawer && cartDrawerOverlay) {
      cartDrawer.classList.remove("active");
      cartDrawerOverlay.classList.remove("active");
      document.body.style.overflow = "";
    }
  }

  if (cartDrawerClose) {
    cartDrawerClose.addEventListener("click", closeCartDrawer);
  }
  if (cartDrawerOverlay) {
    cartDrawerOverlay.addEventListener("click", closeCartDrawer);
  }

  // Expose openCartDrawer globally so cart add events can trigger it
  window.openCartDrawer = openCartDrawer;
  window.closeCartDrawer = closeCartDrawer;

  // 3. Smooth Scroll to Top helper
  const scrollTopBtn = document.getElementById("scrollTopBtn");
  if (scrollTopBtn) {
    window.addEventListener("scroll", function () {
      if (window.scrollY > 300) {
        scrollTopBtn.style.display = "flex";
      } else {
        scrollTopBtn.style.display = "none";
      }
    });

    scrollTopBtn.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }
});
