/**
 * AGY Local Studio: Shared Closed-Form Motion & Transition Primitives
 * Pure functions of time `t` (in seconds) across WeftCut Motifs, OneTake, and HyperFrames.
 * Zero internal mutable state; every output is reproducible at arbitrary seek times.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.AGYMotion = factory();
  }
}(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  function clamp01(v) {
    return v < 0 ? 0 : v > 1 ? 1 : v;
  }

  function lerp(a, b, u) {
    return a + (b - a) * u;
  }

  function invLerp(a, b, v) {
    if (Math.abs(b - a) < 1e-9) return 0;
    return clamp01((v - a) / (b - a));
  }

  function remap(inMin, inMax, outMin, outMax, v) {
    return lerp(outMin, outMax, invLerp(inMin, inMax, v));
  }

  function smoothstep(edge0, edge1, x) {
    var u = invLerp(edge0, edge1, x);
    return u * u * (3 - 2 * u);
  }

  function sampleCubic(a, b, c, t) {
    return ((a * t + b) * t + c) * t;
  }

  function sampleCubicDeriv(a, b, c, t) {
    return (3 * a * t + 2 * b) * t + c;
  }

  /**
   * Build a deterministic cubic-bezier easing function f(u) -> [0, 1].
   */
  function cubicBezier(x1, y1, x2, y2) {
    var cx = 3 * x1;
    var bx = 3 * (x2 - x1) - cx;
    var ax = 1 - cx - bx;
    var cy = 3 * y1;
    var by = 3 * (y2 - y1) - cy;
    var ay = 1 - cy - by;

    function solveX(x) {
      var t2 = x;
      for (var i = 0; i < 8; i++) {
        var xEst = sampleCubic(ax, bx, cx, t2) - x;
        if (Math.abs(xEst) < 1e-6) return t2;
        var d = sampleCubicDeriv(ax, bx, cx, t2);
        if (Math.abs(d) < 1e-6) break;
        t2 -= xEst / d;
      }
      var lo = 0;
      var hi = 1;
      t2 = clamp01(x);
      for (var j = 0; j < 20; j++) {
        var val = sampleCubic(ax, bx, cx, t2);
        if (Math.abs(val - x) < 1e-6) break;
        if (x > val) lo = t2;
        else hi = t2;
        t2 = 0.5 * (lo + hi);
      }
      return t2;
    }

    return function ease(u) {
      var x = clamp01(u);
      return sampleCubic(ay, by, cy, solveX(x));
    };
  }

  /**
   * Calibrated motion curves mapped from studied reference Shorts.
   */
  var CURVE_TUPLES = {
    appleOut: [0.16, 1.0, 0.3, 1.0],
    ghostEcho: [0.38, 0.0, 0.0, 1.0],
    fusionEase85: [0.85, 0.0, 0.15, 1.0],
    smoothMask: [0.7, 0.0, 0.3, 1.0],
    snapExit: [0.6, 0.0, 0.9, 0.35],
    outCubic: [0.33, 1.0, 0.68, 1.0]
  };

  var CURVES = {
    appleOut: cubicBezier(0.16, 1.0, 0.3, 1.0),
    ghostEcho: cubicBezier(0.38, 0.0, 0.0, 1.0),
    fusionEase85: cubicBezier(0.85, 0.0, 0.15, 1.0),
    smoothMask: cubicBezier(0.7, 0.0, 0.3, 1.0),
    snapExit: cubicBezier(0.6, 0.0, 0.9, 0.35),
    outCubic: cubicBezier(0.33, 1.0, 0.68, 1.0)
  };

  function resolveEase(curve) {
    if (typeof curve === 'function') return curve;
    if (typeof curve === 'string' && CURVES[curve]) return CURVES[curve];
    if (Array.isArray(curve) && curve.length === 4) {
      return cubicBezier(curve[0], curve[1], curve[2], curve[3]);
    }
    return CURVES.appleOut;
  }

  /**
   * Closed-form damped harmonic spring evaluated purely from elapsed time localT >= 0.
   */
  function spring(localT, opts) {
    var o = opts || {};
    var from = o.from !== undefined ? o.from : 0;
    var to = o.to !== undefined ? o.to : 1;
    var k = o.stiffness !== undefined ? o.stiffness : 180;
    var c = o.damping !== undefined ? o.damping : 18;
    var m = o.mass !== undefined ? o.mass : 0.8;

    if (localT <= 0) return from;
    var delta = to - from;
    if (Math.abs(delta) < 1e-9) return to;

    var omega0 = Math.sqrt(k / m);
    var zeta = c / (2 * Math.sqrt(k * m));

    if (zeta < 1) {
      var omegaD = omega0 * Math.sqrt(1 - zeta * zeta);
      var env = Math.exp(-zeta * omega0 * localT);
      var norm = 1 - env * (Math.cos(omegaD * localT) + (zeta * omega0 / omegaD) * Math.sin(omegaD * localT));
      return from + delta * norm;
    }
    if (Math.abs(zeta - 1) < 1e-4) {
      var envCrit = Math.exp(-omega0 * localT);
      var normCrit = 1 - envCrit * (1 + omega0 * localT);
      return from + delta * normCrit;
    }
    var root = omega0 * Math.sqrt(zeta * zeta - 1);
    var r1 = -omega0 * zeta + root;
    var r2 = -omega0 * zeta - root;
    var c2 = (r1) / (r1 - r2);
    var c1 = 1 - c2;
    var normOver = 1 - (c1 * Math.exp(r1 * localT) + c2 * Math.exp(r2 * localT));
    return from + delta * normOver;
  }

  /**
   * Normalized per-glyph stagger timing (used by Apple Follower & per-letter shutter motion).
   */
  function charProgress(t, t0, index, opts) {
    var o = opts || {};
    var fps = o.fps || 60;
    var staggerS = o.staggerS !== undefined ? o.staggerS : (o.staggerFrames || 2) / fps;
    var durationS = o.durationS !== undefined ? o.durationS : (o.resolveFrames || 10) / (o.refFps || 30);
    var ease = resolveEase(o.curve || CURVES.appleOut);
    var start = t0 + index * staggerS;
    var u = durationS > 1e-6 ? clamp01((t - start) / durationS) : (t >= start ? 1 : 0);
    return {
      u: u,
      eased: ease(u),
      active: t >= start && u < 1,
      started: t >= start
    };
  }

  /**
   * Reference hRjZf_sg9GQ: Apple Follower per-character stagger.
   * Zero bounce Out Cubic / appleOut rise (-0.3em -> 0), blur resolve (6px -> 0), per-glyph shadow.
   */
  function appleFollowerChar(t, t0, index, opts) {
    var o = opts || {};
    var p = charProgress(t, t0, index, {
      fps: o.fps || 30,
      refFps: o.fps || 30,
      staggerFrames: o.staggerFrames !== undefined ? o.staggerFrames : 2,
      resolveFrames: o.resolveFrames !== undefined ? o.resolveFrames : 10,
      staggerS: o.staggerS,
      durationS: o.durationS,
      curve: o.curve || CURVES.appleOut
    });
    var e = p.eased;
    var riseEm = o.riseEm !== undefined ? o.riseEm : -0.3;
    var startBlur = o.startBlurPx !== undefined ? o.startBlurPx : 6;
    return {
      opacity: clamp01(Math.pow(e, 0.78)),
      translateYEm: lerp(riseEm, 0, e),
      blurPx: lerp(startBlur, 0, e),
      shadowAlpha: lerp(0, o.maxShadowAlpha !== undefined ? o.maxShadowAlpha : 0.45, e),
      scale: lerp(o.startScale !== undefined ? o.startScale : 0.96, 1, e),
      u: p.u,
      eased: e
    };
  }

  /**
   * Reference NyOTPC5aQog: Ghost Echo 20% dual-layer kinetic slide & outward trail.
   * Residue expands + blurs at 20% opacity while incoming layer glides to focus.
   */
  function ghostEchoPair(t, t0, opts) {
    var o = opts || {};
    var durationS = o.durationS !== undefined ? o.durationS : 0.48;
    var slideDistancePx = o.slideDistancePx !== undefined ? o.slideDistancePx : 72;
    var echoOpacityMax = o.echoOpacity !== undefined ? o.echoOpacity : 0.2;
    var ease = resolveEase(o.curve || CURVES.ghostEcho);
    var u = clamp01((t - t0) / Math.max(1e-4, durationS));
    var e = ease(u);

    var ghostU = clamp01((t - t0) / Math.max(1e-4, durationS * 1.15));
    var ge = ease(ghostU);
    var ghostFade = 1 - smoothstep(0.15, 1.0, ghostU);

    return {
      u: u,
      eased: e,
      ghost: {
        opacity: echoOpacityMax * ghostFade,
        scale: lerp(1.0, o.ghostScaleMax !== undefined ? o.ghostScaleMax : 1.48, ge),
        translateX: lerp(0, o.ghostDriftPx !== undefined ? o.ghostDriftPx : -36, ge),
        blurPx: lerp(1.5, o.ghostBlurMax !== undefined ? o.ghostBlurMax : 18, ge)
      },
      incoming: {
        opacity: smoothstep(0.0, 0.28, u),
        scale: lerp(o.inStartScale !== undefined ? o.inStartScale : 1.08, 1.0, e),
        translateX: lerp(slideDistancePx, 0, e),
        blurPx: lerp(o.inStartBlurPx !== undefined ? o.inStartBlurPx : 10, 0, Math.pow(e, 1.15))
      }
    };
  }

  /**
   * Reference L3HeXpHpxaY: Rolling Text Cylinder / Slot-Machine Drum per column.
   * Uses analytic derivative of curve to drive directional Y blur peaking at mid-roll.
   */
  function rollingSlotColumn(t, t0, colIndex, opts) {
    var o = opts || {};
    var steps = Math.max(1, o.steps !== undefined ? o.steps : 6);
    var cellHeightPx = o.cellHeightPx !== undefined ? o.cellHeightPx : 112;
    var colStaggerS = o.colStaggerS !== undefined ? o.colStaggerS : 0.042;
    var durationS = o.durationS !== undefined ? o.durationS : 0.72;
    var maxBlurPx = o.maxBlurPx !== undefined ? o.maxBlurPx : 14;
    var ease = resolveEase(o.curve || CURVES.fusionEase85);

    var localT = t - (t0 + colIndex * colStaggerS);
    var u = clamp01(localT / Math.max(1e-4, durationS));
    var e = ease(u);

    var du = 0.004;
    var uPrev = clamp01(u - du);
    var uNext = clamp01(u + du);
    var speedNorm = (u > 0 && u < 1) ? (ease(uNext) - ease(uPrev)) / Math.max(1e-5, uNext - uPrev) : 0;
    var peakRef = 2.6;
    var blurY = u >= 1 || u <= 0 ? 0 : clamp01(speedNorm / peakRef) * maxBlurPx;

    var totalTravel = steps * cellHeightPx;
    var currentOffset = -e * totalTravel;
    return {
      u: u,
      eased: e,
      offsetYPx: currentOffset,
      blurYPx: blurY,
      opacity: smoothstep(0.0, 0.08, u),
      settled: u >= 1
    };
  }

  /**
   * Reference ZcmcHeWWAuI: 3D spatial depth Z-push + optical Focal-Plane DoF lens blur.
   */
  function spatial3DCameraWord(cameraZ, wordZ, opts) {
    var o = opts || {};
    var focalZ = o.focalZ !== undefined ? o.focalZ : cameraZ;
    var dofRange = o.dofRange !== undefined ? o.dofRange : 420;
    var maxDofBlurPx = o.maxDofBlurPx !== undefined ? o.maxDofBlurPx : 9;
    var baseFocalDist = o.baseFocalDist !== undefined ? o.baseFocalDist : 900;

    var relToCam = wordZ - cameraZ;
    var denom = Math.max(120, baseFocalDist - relToCam);
    var perspectiveScale = baseFocalDist / denom;

    var distFromFocus = Math.abs(wordZ - focalZ);
    var dofRatio = clamp01(distFromFocus / Math.max(1, dofRange));
    var dofBlurPx = dofRatio * dofRatio * maxDofBlurPx;

    var nearClipFade = 1 - smoothstep(baseFocalDist * 0.65, baseFocalDist * 0.92, relToCam);
    var farFade = 1 - smoothstep(baseFocalDist * 0.9, baseFocalDist * 1.8, -relToCam);

    return {
      perspectiveScale: perspectiveScale,
      dofBlurPx: dofBlurPx,
      opacity: clamp01(Math.min(nearClipFade, farFade)),
      relToCam: relToCam
    };
  }

  /**
   * Reference ZcmcHeWWAuI / DESIGN.md: Mixed-Voice typographic role profiles.
   * Ensures at least 2 complementary font voices + tight display tracking (-0.04em).
   */
  var VOICE_ROLES = {
    hero: {
      fontFamily: "'Inter Tight', 'Inter', sans-serif",
      fontWeight: 800,
      fontStyle: 'normal',
      letterSpacingEm: -0.04,
      lineHeight: 0.96,
      sizeRatio: 1.0
    },
    accent: {
      fontFamily: "'Instrument Serif', 'Fraunces', serif",
      fontWeight: 400,
      fontStyle: 'italic',
      letterSpacingEm: -0.015,
      lineHeight: 1.02,
      sizeRatio: 1.06
    },
    connector: {
      fontFamily: "'Inter Tight', 'Inter', sans-serif",
      fontWeight: 300,
      fontStyle: 'normal',
      letterSpacingEm: 0.04,
      lineHeight: 1.15,
      sizeRatio: 0.52
    },
    telemetry: {
      fontFamily: "'JetBrains Mono', 'Geist Mono', monospace",
      fontWeight: 500,
      fontStyle: 'normal',
      letterSpacingEm: 0.02,
      lineHeight: 1.1,
      sizeRatio: 0.42
    }
  };

  function mixedVoiceRole(role) {
    return VOICE_ROLES[role] || VOICE_ROLES.hero;
  }

  /**
   * Reference 4tx33YWabuE: Structured extra kinetic text moves for rhythmic variety.
   */
  function kinetic20Move(kind, t, t0, opts) {
    var o = opts || {};
    var durationS = o.durationS !== undefined ? o.durationS : 0.45;
    var u = clamp01((t - t0) / Math.max(1e-4, durationS));
    var ease = resolveEase(o.curve || CURVES.appleOut);
    var e = ease(u);

    switch (kind) {
      case 'tracking-expand':
        return { opacity: smoothstep(0, 0.25, u), letterSpacingEm: lerp(0.18, o.targetTrackingEm !== undefined ? o.targetTrackingEm : -0.03, e), blurPx: lerp(4, 0, e), translateYPx: 0, scale: lerp(1.06, 1.0, e) };
      case 'split-reveal':
        return { opacity: u > 0 ? 1 : 0, clipInsetPct: lerp(50, 0, e), translateYPx: lerp(18, 0, e), blurPx: lerp(3, 0, e), scale: 1 };
      case 'strike-rotate':
        return { opacity: smoothstep(0, 0.2, u), rotateDeg: lerp(-12, 0, e), scale: lerp(1.22, 1.0, e), blurPx: lerp(6, 0, e), translateYPx: lerp(24, 0, e) };
      case 'decode-marker':
        return { opacity: u > 0 ? 1 : 0, revealRatio: e, cursorActive: u > 0 && u < 0.96, blurPx: 0, translateYPx: 0, scale: 1 };
      case 'blur-focus':
      default:
        return { opacity: smoothstep(0, 0.35, u), blurPx: lerp(14, 0, e), scale: lerp(1.12, 1.0, e), translateYPx: 0 };
    }
  }

  /**
   * Transition 1 (XLMHpphSxJQ): Natural Foreground Occlusion Wipe.
   */
  function foregroundOcclusionWipe(t, tStart, opts) {
    var o = opts || {};
    var durationS = o.durationS !== undefined ? o.durationS : 0.46;
    var u = clamp01((t - tStart) / Math.max(1e-4, durationS));
    var e = CURVES.fusionEase85(u);
    var sweepPct = lerp(100, -10, e);
    return {
      u: u,
      eased: e,
      clipRightPct: clamp01(sweepPct / 100) * 100,
      clipPathPolygon: 'polygon(0% 0%, ' + (100 - clamp01(1 - sweepPct / 100) * 100).toFixed(2) + '% 0%, ' + Math.max(0, 100 - clamp01(1 - sweepPct / 100) * 100 - 4).toFixed(2) + '% 100%, 0% 100%)',
      shutterBlurPx: Math.sin(u * Math.PI) * (o.maxBlurPx !== undefined ? o.maxBlurPx : 12),
      active: u > 0 && u < 1
    };
  }

  /**
   * Transition 2 (wkbAl3Y2DnM): Cutout Frame Hold Slide-In with 180-deg shutter blur & snap.
   */
  function cutoutFrameHoldSlide(t, tStart, opts) {
    var o = opts || {};
    var durationS = o.durationS !== undefined ? o.durationS : 0.22;
    var fromXPx = o.fromXPx !== undefined ? o.fromXPx : -920;
    var fromYPx = o.fromYPx !== undefined ? o.fromYPx : 0;
    var localT = t - tStart;
    var u = clamp01(localT / Math.max(1e-4, durationS));
    var e = CURVES.appleOut(u);
    var posX = lerp(fromXPx, 0, e);
    var posY = lerp(fromYPx, 0, e);
    var speedFactor = Math.sin(u * Math.PI);
    return {
      u: u,
      eased: e,
      translateXPx: posX,
      translateYPx: posY,
      motionBlurXPx: Math.abs(fromXPx) > 10 ? speedFactor * (o.maxBlurPx !== undefined ? o.maxBlurPx : 18) : 0,
      motionBlurYPx: Math.abs(fromYPx) > 10 ? speedFactor * (o.maxBlurPx !== undefined ? o.maxBlurPx : 18) : 0,
      handedOff: u >= 1,
      active: localT >= 0 && u < 1
    };
  }

  /**
   * Transition 3 (rK6t1utoWrc): Smooth Mask Reveal with mid-peak horizontal smear & push-in.
   */
  function smoothMaskReveal(t, tStart, opts) {
    var o = opts || {};
    var durationS = o.durationS !== undefined ? o.durationS : 0.5;
    var u = clamp01((t - tStart) / Math.max(1e-4, durationS));
    var e = CURVES.smoothMask(u);
    var vel = Math.sin(u * Math.PI);
    var edgePct = e * 108;
    var featherPct = o.featherPct !== undefined ? o.featherPct : 4;
    return {
      u: u,
      eased: e,
      maskEdgePct: edgePct,
      featherPct: featherPct,
      edgeBlurPx: vel * (o.maxBlurPx !== undefined ? o.maxBlurPx : 16),
      outgoingScale: lerp(1.0, 1.05, e),
      incomingScale: lerp(1.04, 1.0, e),
      active: u > 0 && u < 1
    };
  }

  /**
   * Transition 4 (ruwVARuOkqA): Angled Feathered Split Wipe + Counter-Zoom.
   */
  function angledSplitZoom(t, tStart, opts) {
    var o = opts || {};
    var durationS = o.durationS !== undefined ? o.durationS : 0.24;
    var skewOffsetPct = o.skewOffsetPct !== undefined ? o.skewOffsetPct : 14;
    var u = clamp01((t - tStart) / Math.max(1e-4, durationS));
    var e = CURVES.smoothMask(u);
    var topCut = clamp01(e * 1.12) * 100;
    var botCut = clamp01(e * 1.12 - skewOffsetPct / 100) * 100;
    return {
      u: u,
      eased: e,
      clipPolygon: 'polygon(0% 0%, ' + topCut.toFixed(2) + '% 0%, ' + botCut.toFixed(2) + '% 100%, 0% 100%)',
      outgoingScale: lerp(1.0, 1.06, e),
      incomingScale: lerp(1.08, 1.0, e),
      featherBlurPx: Math.sin(u * Math.PI) * 8,
      active: u > 0 && u < 1
    };
  }

  /**
   * Maciek Sulima (yRsK2JyfMGM) Rule 1 & 2: Split-S-Curve Handoff along a single directional axis.
   * Outgoing element accelerates out (u^3.2) and incoming element decelerates in (1-(1-u)^3.6),
   * uniting both into one continuous S-curve peaking right across tSwap.
   */
  function splitSCurveHandoff(t, tSwap, opts) {
    var o = opts || {};
    var durOut = Math.max(0.06, o.durOutS !== undefined ? o.durOutS : 0.24);
    var durIn = Math.max(0.06, o.durInS !== undefined ? o.durInS : 0.34);
    var dist = o.distancePx !== undefined ? o.distancePx : 56;
    var axis = o.axis === 'x' ? 'x' : 'y';
    var dir = o.direction === -1 ? -1 : 1; // 1 = move upward/leftward across handoff

    var uOut = clamp01((t - (tSwap - durOut)) / durOut);
    var eOut = Math.pow(uOut, 3.2); // slow start -> rapid acceleration into swap
    var uIn = clamp01((t - tSwap) / durIn);
    var eIn = 1 - Math.pow(1 - uIn, 3.6); // rapid launch at swap -> velvety slow settle

    var outOffset = -dir * eOut * dist;
    var inOffset = dir * (1 - eIn) * dist;
    var outBlur = (uOut > 0 && uOut < 1) ? Math.pow(uOut, 2.0) * (o.maxBlurPx !== undefined ? o.maxBlurPx : 10) : 0;
    var inBlur = (uIn > 0 && uIn < 1) ? Math.pow(1 - uIn, 2.2) * (o.maxBlurPx !== undefined ? o.maxBlurPx : 10) : 0;

    return {
      axis: axis,
      outgoing: {
        offsetPx: outOffset,
        opacity: t >= tSwap ? 0 : (1 - smoothstep(0.55, 1.0, uOut)),
        blurPx: outBlur
      },
      incoming: {
        offsetPx: inOffset,
        opacity: t < tSwap ? 0 : smoothstep(0.0, 0.22, uIn),
        blurPx: inBlur,
        settled: uIn >= 1
      }
    };
  }

  /**
   * Maciek Sulima (yRsK2JyfMGM): Asymmetric 3-tier Reels caption hierarchy (lead / HERO / tail).
   */
  function asymmetricCaptionLayout(words, heroIdx) {
    var list = Array.isArray(words) ? words : [];
    var hi = (heroIdx !== undefined && heroIdx >= 0 && heroIdx < list.length) ? heroIdx : Math.floor(list.length / 2);
    return list.map(function (w, idx) {
      var isHero = idx === hi;
      return {
        word: String(w),
        tier: isHero ? 'hero' : (idx < hi ? 'lead' : 'tail'),
        scale: isHero ? 1.55 : 0.78,
        weight: isHero ? 900 : 600,
        italic: isHero
      };
    });
  }

  /**
   * Gaku Lange (SmsNAtaLR9I): Match-Cut Split Screen trajectory alignment & reveal.
   */
  function matchCutSplitWipe(t, tStart, opts) {
    var o = opts || {};
    var dur = Math.max(0.08, o.durationS !== undefined ? o.durationS : 0.36);
    var targetSplit = clamp01(o.splitRatio !== undefined ? o.splitRatio : 0.5);
    var u = clamp01((t - tStart) / dur);
    var e = CURVES.appleOut(u);
    return {
      u: u,
      splitPct: lerp(0, targetSplit * 100, e),
      seamOpacity: smoothstep(0.0, 0.25, u),
      settled: u >= 1
    };
  }

  /**
   * PeeJ ENT (G-DHQAzulyU): 2D Virtual Camera Typography over a spatial word canvas.
   * Shifts camera arrival 2-3 frames (-83ms default) early before each audio word stop
   * so the eye lands squarely on the cluster right when the ear hears the beat.
   */
  function camera2DTypographyState(t, stops, opts) {
    var o = opts || {};
    var list = Array.isArray(stops) && stops.length ? stops : [{ t: 0, x: 0, y: 0, zoom: 1, rotateDeg: 0 }];
    var leadS = o.preBeatLeadS !== undefined ? o.preBeatLeadS : 0.083;
    var transS = Math.max(0.08, o.transitionS !== undefined ? o.transitionS : 0.28);
    var maxBlur = o.maxBlurPx !== undefined ? o.maxBlurPx : 7;
    var tAdj = t + leadS;

    var idx = 0;
    for (var i = 0; i < list.length; i++) {
      if (tAdj >= list[i].t) idx = i;
    }
    var curr = list[idx];
    var prev = idx > 0 ? list[idx - 1] : curr;
    var u = idx > 0 ? clamp01((tAdj - curr.t) / transS) : 1;
    var e = CURVES.smoothMask(u);
    var vel = (idx > 0 && u > 0 && u < 1) ? Math.sin(u * Math.PI) : 0;

    return {
      stopIndex: idx,
      camX: lerp(prev.x || 0, curr.x || 0, e),
      camY: lerp(prev.y || 0, curr.y || 0, e),
      zoom: lerp(prev.zoom || 1, curr.zoom || 1, e),
      rotateDeg: lerp(prev.rotateDeg || 0, curr.rotateDeg || 0, e),
      blurPx: vel * maxBlur,
      strokeProgress: clamp01((idx + e) / Math.max(1, list.length - 1))
    };
  }

  /**
   * Editor Keling (RhVB8WPLJAI): Staggered Narrative Cluster Word & Highlight Swipe.
   * Words enter briskly and accumulate together on screen until clauseEndS.
   */
  function narrativeClusterWord(t, wordStartS, opts) {
    var o = opts || {};
    var dur = Math.max(0.06, o.durationS !== undefined ? o.durationS : 0.22);
    var u = clamp01((t - wordStartS) / dur);
    var e = CURVES.appleOut(u);
    var swU = clamp01((t - (wordStartS + 0.06)) / 0.24);
    var swE = CURVES.smoothMask(swU);
    return {
      visible: t >= wordStartS,
      opacity: smoothstep(0.0, 0.28, u),
      translateYPx: lerp(22, 0, e),
      scale: lerp(0.90, 1.0, e),
      highlightSweepPct: swE * 100
    };
  }

  /**
   * aayusucks (BWRdNeNkph4): Golden-Ratio 1.618x Scale & 8pt Grid Typography Calculator.
   */
  function goldenTypeScale(basePx) {
    var b = Math.max(12, basePx || 16);
    function snap8(v) { return Math.max(8, Math.round(v / 8) * 8); }
    var sub = snap8(b * 1.618);
    var head = snap8(b * 1.618 * 1.618);
    var disp = snap8(head * 1.618);
    return {
      bodyPx: snap8(b),
      bodyLeadingPx: snap8(b * 1.5),
      subheadPx: sub,
      headlinePx: head,
      headlineLeadingPx: Math.round(head * 1.2),
      displayPx: disp,
      maxCharsPerLine: 65,
      gridUnitPx: 8
    };
  }

  return {
    clamp01: clamp01,
    lerp: lerp,
    invLerp: invLerp,
    remap: remap,
    smoothstep: smoothstep,
    cubicBezier: cubicBezier,
    CURVE_TUPLES: CURVE_TUPLES,
    CURVES: CURVES,
    spring: spring,
    charProgress: charProgress,
    appleFollowerChar: appleFollowerChar,
    ghostEchoPair: ghostEchoPair,
    rollingSlotColumn: rollingSlotColumn,
    spatial3DCameraWord: spatial3DCameraWord,
    mixedVoiceRole: mixedVoiceRole,
    VOICE_ROLES: VOICE_ROLES,
    kinetic20Move: kinetic20Move,
    foregroundOcclusionWipe: foregroundOcclusionWipe,
    cutoutFrameHoldSlide: cutoutFrameHoldSlide,
    smoothMaskReveal: smoothMaskReveal,
    angledSplitZoom: angledSplitZoom,
    splitSCurveHandoff: splitSCurveHandoff,
    asymmetricCaptionLayout: asymmetricCaptionLayout,
    matchCutSplitWipe: matchCutSplitWipe,
    camera2DTypographyState: camera2DTypographyState,
    narrativeClusterWord: narrativeClusterWord,
    goldenTypeScale: goldenTypeScale
  };
}));
