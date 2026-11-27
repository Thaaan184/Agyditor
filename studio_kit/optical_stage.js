/**
 * AGY Local Studio v2: GLSL Optical Transition Shaders & SVG Glow Nib Engine
 * Runs with Three.js r186 ShaderPass (MotionTileWhip, OpticalRadialMatch, FlashCutoutStrobe)
 * plus seek-deterministic SVG Trim Path + emitter glow nib (reference 5kLbhiIc63w).
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory(require('./motion_primitives.js'));
  } else {
    root.AGYOptics = factory(root.AGYMotion);
  }
}(typeof globalThis !== 'undefined' ? globalThis : this, function (M) {
  'use strict';

  /**
   * GLSL Shader 1 (Reference uSFLQ5bfKps): After Effects Motion Tile + Mirror Edges + Velocity Blur.
   */
  var MotionTileWhipShader = {
    uniforms: {
      tDiffuse: { value: null },
      uOffset: { value: [0, 0] },
      uBlurVec: { value: [0, 0] },
      uTileScale: { value: 1.0 },
      uMirrorEdges: { value: 1.0 }
    },
    vertexShader: [
      'varying vec2 vUv;',
      'void main() {',
      '  vUv = uv;',
      '  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);',
      '}'
    ].join('\n'),
    fragmentShader: [
      'uniform sampler2D tDiffuse;',
      'uniform vec2 uOffset;',
      'uniform vec2 uBlurVec;',
      'uniform float uTileScale;',
      'uniform float uMirrorEdges;',
      'varying vec2 vUv;',
      '',
      'vec2 tileCoord(vec2 p) {',
      '  if (uMirrorEdges > 0.5) {',
      '    vec2 m = mod(p, 2.0);',
      '    return vec2(m.x > 1.0 ? 2.0 - m.x : m.x, m.y > 1.0 ? 2.0 - m.y : m.y);',
      '  }',
      '  return fract(p);',
      '}',
      '',
      'void main() {',
      '  vec2 base = (vUv - 0.5) * uTileScale + 0.5 + uOffset;',
      '  vec4 acc = vec4(0.0);',
      '  const int TAPS = 9;',
      '  for (int i = 0; i < TAPS; i++) {',
      '    float k = (float(i) / float(TAPS - 1)) - 0.5;',
      '    vec2 sampleUv = tileCoord(base + uBlurVec * k);',
      '    acc += texture2D(tDiffuse, clamp(sampleUv, 0.001, 0.999));',
      '  }',
      '  gl_FragColor = acc / float(TAPS);',
      '}'
    ].join('\n')
  };

  /**
   * GLSL Shader 2 (Reference 9c9PVAQXiLU): Radial Optical Zoom Blur + Rotation + Chromatic Split.
   */
  var OpticalRadialMatchShader = {
    uniforms: {
      tDiffuse: { value: null },
      uZoom: { value: 1.0 },
      uAngleRad: { value: 0.0 },
      uRadialBlur: { value: 0.0 },
      uChromatic: { value: 0.0 }
    },
    vertexShader: [
      'varying vec2 vUv;',
      'void main() {',
      '  vUv = uv;',
      '  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);',
      '}'
    ].join('\n'),
    fragmentShader: [
      'uniform sampler2D tDiffuse;',
      'uniform float uZoom;',
      'uniform float uAngleRad;',
      'uniform float uRadialBlur;',
      'uniform float uChromatic;',
      'varying vec2 vUv;',
      '',
      'vec2 warpUv(vec2 uv, float zoomMul) {',
      '  vec2 d = (uv - 0.5) / max(0.25, uZoom * zoomMul);',
      '  float c = cos(uAngleRad);',
      '  float s = sin(uAngleRad);',
      '  return vec2(d.x * c - d.y * s, d.x * s + d.y * c) + 0.5;',
      '}',
      '',
      'vec2 mirrorClamp(vec2 p) {',
      '  vec2 m = mod(p, 2.0);',
      '  return clamp(vec2(m.x > 1.0 ? 2.0 - m.x : m.x, m.y > 1.0 ? 2.0 - m.y : m.y), 0.001, 0.999);',
      '}',
      '',
      'void main() {',
      '  vec3 col = vec3(0.0);',
      '  const int SAMPLES = 8;',
      '  for (int i = 0; i < SAMPLES; i++) {',
      '    float f = float(i) / float(SAMPLES - 1);',
      '    float scaleShift = 1.0 - f * uRadialBlur * 0.22;',
      '    vec2 uvR = mirrorClamp(warpUv(vUv, scaleShift * (1.0 + uChromatic * 0.025)));',
      '    vec2 uvG = mirrorClamp(warpUv(vUv, scaleShift));',
      '    vec2 uvB = mirrorClamp(warpUv(vUv, scaleShift * (1.0 - uChromatic * 0.025)));',
      '    col.r += texture2D(tDiffuse, uvR).r;',
      '    col.g += texture2D(tDiffuse, uvG).g;',
      '    col.b += texture2D(tDiffuse, uvB).b;',
      '  }',
      '  gl_FragColor = vec4(col / float(SAMPLES), 1.0);',
      '}'
    ].join('\n')
  };

  /**
   * GLSL Shader 3 (Reference dHAx3HSVDLA): Adjustment Layer Flash Strobe (Tint + Invert + Scale Punch).
   */
  var FlashCutoutStrobeShader = {
    uniforms: {
      tDiffuse: { value: null },
      uInvertMix: { value: 0.0 },
      uTintColor: { value: [0.055, 0.647, 0.914] },
      uTintMix: { value: 0.0 },
      uScalePunch: { value: 1.0 },
      uFlashGain: { value: 1.0 }
    },
    vertexShader: [
      'varying vec2 vUv;',
      'void main() {',
      '  vUv = uv;',
      '  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);',
      '}'
    ].join('\n'),
    fragmentShader: [
      'uniform sampler2D tDiffuse;',
      'uniform float uInvertMix;',
      'uniform vec3 uTintColor;',
      'uniform float uTintMix;',
      'uniform float uScalePunch;',
      'uniform float uFlashGain;',
      'varying vec2 vUv;',
      '',
      'void main() {',
      '  vec2 uv = (vUv - 0.5) / max(0.5, uScalePunch) + 0.5;',
      '  vec4 base = texture2D(tDiffuse, clamp(uv, 0.001, 0.999));',
      '  vec3 inverted = 1.0 - base.rgb;',
      '  vec3 mixed = mix(base.rgb, inverted, clamp(uInvertMix, 0.0, 1.0));',
      '  float lum = dot(mixed, vec3(0.299, 0.587, 0.114));',
      '  vec3 tinted = mix(mixed, mix(vec3(lum * 0.25), uTintColor, lum), clamp(uTintMix, 0.0, 1.0));',
      '  gl_FragColor = vec4(tinted * uFlashGain, base.a);',
      '}'
    ].join('\n')
  };

  /**
   * Reference 5kLbhiIc63w: Seek-deterministic SVG Trim-Path Handwriting Reveal + Glowing Nib.
   * Updates stroke-dashoffset and computes exact tip (x, y) on the vector curve for t.
   */
  function glowSignaturePath(pathEl, nibEl, t, t0, durationS, opts) {
    var o = opts || {};
    var dur = Math.max(0.1, durationS || 2.2);
    var totalLen = o.totalLength || (pathEl && typeof pathEl.getTotalLength === 'function' ? pathEl.getTotalLength() : 1000);
    var u = M.clamp01((t - t0) / dur);
    var e = M.CURVES.appleOut(u);
    var drawnLen = totalLen * e;

    if (pathEl) {
      pathEl.style.strokeDasharray = totalLen.toFixed(2);
      pathEl.style.strokeDashoffset = Math.max(0, totalLen - drawnLen).toFixed(2);
      pathEl.style.opacity = u > 0 ? '1' : '0';
    }

    var pt = { x: 0, y: 0 };
    if (pathEl && typeof pathEl.getPointAtLength === 'function' && totalLen > 0) {
      pt = pathEl.getPointAtLength(Math.min(totalLen, drawnLen));
    }

    var nibFadeIn = M.smoothstep(0.0, 0.06, u);
    var nibFadeOut = 1 - M.smoothstep(0.90, 1.0, u);
    var nibAlpha = nibFadeIn * nibFadeOut;
    if (nibEl) {
      nibEl.style.opacity = nibAlpha.toFixed(4);
      nibEl.style.transform = 'translate3d(' + pt.x.toFixed(2) + 'px,' + pt.y.toFixed(2) + 'px,0)';
    }

    return {
      u: u,
      eased: e,
      drawnLen: drawnLen,
      totalLen: totalLen,
      tipX: pt.x,
      tipY: pt.y,
      nibAlpha: nibAlpha
    };
  }

  /**
   * Helper: Build a CanvasTexture carrying crisp high-DPI text wrapping a Three.js CylinderGeometry
   * (Reference gsS7uvyhYvI: CC Cylinder orbital ribbon around 3D hero object).
   */
  function createCylinderRibbonTexture(THREE, text, opts) {
    var o = opts || {};
    var canvas = document.createElement('canvas');
    canvas.width = o.width || 2048;
    canvas.height = o.height || 256;
    var ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (o.bandColor) {
      ctx.fillStyle = o.bandColor;
      ctx.fillRect(0, 38, canvas.width, canvas.height - 76);
    }

    var baseSize = o.fontSizePx || 118;
    var repeatCount = o.repeatCount || 2;
    var stepX = canvas.width / repeatCount;
    var family = o.fontFamily || '"Oswald", sans-serif';
    var weight = o.fontWeight || '700';

    ctx.font = weight + ' ' + baseSize + 'px ' + family;
    var measured = Math.max(10, ctx.measureText(text).width);
    var maxSlot = stepX * 0.84;
    var fittedSize = measured > maxSlot ? Math.floor(baseSize * (maxSlot / measured)) : baseSize;

    ctx.font = weight + ' ' + fittedSize + 'px ' + family;
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'center';
    ctx.fillStyle = o.textColor || '#F8FAFC';

    for (var i = 0; i < repeatCount; i++) {
      ctx.fillText(text, stepX * (i + 0.5), canvas.height * 0.52);
    }

    var tex = new THREE.CanvasTexture(canvas);
    tex.wrapS = THREE.RepeatWrapping;
    tex.wrapT = THREE.ClampToEdgeWrapping;
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = 8;
    tex.needsUpdate = true;
    return tex;
  }

  return {
    MotionTileWhipShader: MotionTileWhipShader,
    OpticalRadialMatchShader: OpticalRadialMatchShader,
    FlashCutoutStrobeShader: FlashCutoutStrobeShader,
    glowSignaturePath: glowSignaturePath,
    createCylinderRibbonTexture: createCylinderRibbonTexture
  };
}));
