(function () {
  var box = document.getElementById("hero3d");
  if (!box) return;
  var hero = box.closest(".hero");
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  if (!window.matchMedia("(min-width: 761px)").matches) return;

  var s = document.createElement("script");
  s.src = "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js";
  s.onload = start;
  document.head.appendChild(s);

  function start() {
    var canvas = box.querySelector("canvas");
    var renderer;
    try {
      renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    } catch (e) { return; }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

    var scene = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(38, 1, 0.1, 50);
    camera.position.set(0, 0, 9.5);
    var group = new THREE.Group();
    scene.add(group);

    // Logo symbol: stacked layers give it visible thickness
    var tex = new THREE.TextureLoader().load(box.dataset.icon, function () {
      hero.classList.add("has-3d");
      resize();
    });
    var LAYERS = 14, SIZE = 3.4, STEP = 0.02;
    var geo = new THREE.PlaneGeometry(SIZE, SIZE);
    for (var i = LAYERS - 1; i >= 0; i--) {
      var k = i / (LAYERS - 1);
      var mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, alphaTest: 0.35 });
      if (i > 0) mat.color.setRGB(0.05 + 0.1 * (1 - k), 0.22 + 0.15 * (1 - k), 0.5 + 0.2 * (1 - k));
      var m = new THREE.Mesh(geo, mat);
      m.position.z = -i * STEP;
      group.add(m);
    }

    // Idea / Code / Deploy orbit
    var tiltG = new THREE.Group();
    tiltG.rotation.x = 0.5;
    tiltG.rotation.z = -0.2;
    group.add(tiltG);
    var spin = new THREE.Group();
    tiltG.add(spin);
    var R = 3.0;
    var ring = new THREE.Mesh(
      new THREE.TorusGeometry(R, 0.014, 8, 160),
      new THREE.MeshBasicMaterial({ color: 0x0eaa9c, transparent: true, opacity: 0.55 })
    );
    ring.rotation.x = Math.PI / 2;
    spin.add(ring);

    var items = [["Idea", 0x0eaa9c], ["Code", 0x0b5cc0], ["Deploy", 0x083971]];
    var tags = [];
    items.forEach(function (it, n) {
      var a = n * (Math.PI * 2 / 3);
      var dot = new THREE.Mesh(new THREE.SphereGeometry(0.17, 24, 16), new THREE.MeshBasicMaterial({ color: it[1] }));
      dot.position.set(Math.cos(a) * R, 0, Math.sin(a) * R);
      spin.add(dot);
      var sp = label(it[0], it[1]);
      scene.add(sp);
      tags.push({ dot: dot, sp: sp });
    });

    function roundRect(x, a, b, w, h, r) {
      x.beginPath();
      x.moveTo(a + r, b);
      x.arcTo(a + w, b, a + w, b + h, r);
      x.arcTo(a + w, b + h, a, b + h, r);
      x.arcTo(a, b + h, a, b, r);
      x.arcTo(a, b, a + w, b, r);
      x.closePath();
    }
    function label(text, hex) {
      var c = document.createElement("canvas");
      c.width = 256; c.height = 96;
      var x = c.getContext("2d");
      x.fillStyle = "rgba(255,255,255,0.94)";
      roundRect(x, 6, 10, 244, 76, 38);
      x.fill();
      x.lineWidth = 4;
      x.strokeStyle = "#" + ("000000" + hex.toString(16)).slice(-6);
      x.stroke();
      x.fillStyle = "#0B2A4A";
      x.font = "700 44px Figtree, Arial, sans-serif";
      x.textAlign = "center";
      x.textBaseline = "middle";
      x.fillText(text, 128, 49);
      var sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(c), transparent: true, depthTest: false }));
      sp.scale.set(1.2, 0.45, 1);
      sp.renderOrder = 10;
      return sp;
    }

    function resize() {
      var w = box.clientWidth, h = box.clientHeight;
      if (!w || !h) return;
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    }
    if (window.ResizeObserver) new ResizeObserver(resize).observe(box);

    var tx = 0, ty = 0;
    window.addEventListener("pointermove", function (e) {
      tx = (e.clientY / window.innerHeight - 0.5) * 0.5;
      ty = (e.clientX / window.innerWidth - 0.5) * 0.9;
    }, { passive: true });

    var visible = false, running = false, t0 = performance.now(), v = new THREE.Vector3();
    function frame(now) {
      if (!visible || document.hidden) { running = false; return; }
      var t = (now - t0) / 1000;
      group.rotation.x += (tx - group.rotation.x) * 0.06;
      group.rotation.y += (ty + Math.sin(t * 0.6) * 0.25 - group.rotation.y) * 0.06;
      group.position.y = Math.sin(t * 1.1) * 0.07;
      spin.rotation.y = t * 0.45;
      tags.forEach(function (g) {
        g.dot.getWorldPosition(v);
        g.sp.position.set(v.x, v.y + 0.45, v.z);
      });
      renderer.render(scene, camera);
      requestAnimationFrame(frame);
    }
    function kick() {
      if (visible && !document.hidden && !running) { running = true; requestAnimationFrame(frame); }
    }
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (en) { visible = en[0].isIntersecting; kick(); }).observe(box);
    } else { visible = true; kick(); }
    document.addEventListener("visibilitychange", kick);
  }
})();
