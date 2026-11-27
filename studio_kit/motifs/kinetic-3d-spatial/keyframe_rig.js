/**
 * AGY Local Studio v2: Composable 4-Axis Keyframe, Speed-Graph & 3D Camera Rig
 * Pure f(t) evaluator unifying Three.js WebGL camera/DoF with synchronized SVG/DOM layers
 * and WeftCut multi-layer sandwich exports.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    var mp = require('./motion_primitives.js');
    module.exports = factory(mp);
  } else {
    root.AGYRig = factory(root.AGYMotion);
  }
}(typeof globalThis !== 'undefined' ? globalThis : this, function (M) {
  'use strict';

  /**
   * Calibrated Speed-Graph curves reverse-engineered from studied After Effects & Fusion rigs.
   */
  var SPEED_GRAPHS = {
    aeWhipOut: M.cubicBezier(0.12, 0.96, 0.18, 1.0),
    aeWhipInOut: M.cubicBezier(0.78, 0.0, 0.18, 1.0),
    aeHardInOut: M.cubicBezier(0.85, 0.0, 0.15, 1.0),
    easyEase: M.cubicBezier(0.42, 0.0, 0.58, 1.0),
    smoothStop: M.cubicBezier(0.16, 1.0, 0.3, 1.0),
    ghostEcho: M.cubicBezier(0.38, 0.0, 0.0, 1.0),
    linear: function (u) { return M.clamp01(u); }
  };

  function resolveCurve(ease) {
    if (typeof ease === 'function') return ease;
    if (typeof ease === 'string' && SPEED_GRAPHS[ease]) return SPEED_GRAPHS[ease];
    if (typeof ease === 'string' && M.CURVES[ease]) return M.CURVES[ease];
    if (Array.isArray(ease) && ease.length === 4) {
      return M.cubicBezier(ease[0], ease[1], ease[2], ease[3]);
    }
    return SPEED_GRAPHS.easyEase;
  }

  function lerpVal(a, b, u) {
    if (Array.isArray(a) && Array.isArray(b)) {
      var out = new Array(a.length);
      for (var i = 0; i < a.length; i++) out[i] = M.lerp(a[i], b[i], u);
      return out;
    }
    return M.lerp(a, b, u);
  }

  function keyTimeSeconds(kf, durationS) {
    if (typeof kf.u === 'number') return M.clamp01(kf.u) * durationS;
    return Number(kf.t || 0);
  }

  /**
   * Evaluate a multi-stop keyframe track at absolute time t.
   * Each keyframe: { u?: [0..1], t?: sec, v: number|number[], ease?: string|bezier, mode?: 'hold'|'spring' }
   */
  function evalTrack(keyframes, t, durationS) {
    if (!keyframes || keyframes.length === 0) return 0;
    var dur = Math.max(1e-4, durationS || 1.0);
    if (keyframes.length === 1) return keyframes[0].v;

    var firstT = keyTimeSeconds(keyframes[0], dur);
    if (t <= firstT) return keyframes[0].v;

    var lastIdx = keyframes.length - 1;
    var lastT = keyTimeSeconds(keyframes[lastIdx], dur);
    if (t >= lastT) return keyframes[lastIdx].v;

    for (var i = 0; i < lastIdx; i++) {
      var k0 = keyframes[i];
      var k1 = keyframes[i + 1];
      var t0 = keyTimeSeconds(k0, dur);
      var t1 = keyTimeSeconds(k1, dur);
      if (t >= t0 && t <= t1) {
        if (k0.mode === 'hold') return k0.v;
        var span = Math.max(1e-5, t1 - t0);
        var localU = M.clamp01((t - t0) / span);
        if (k0.mode === 'spring') {
          var sNorm = M.spring(t - t0, {
            from: 0,
            to: 1,
            stiffness: k0.stiffness || 210,
            damping: k0.damping || 16,
            mass: k0.mass || 0.75
          });
          return lerpVal(k0.v, k1.v, sNorm);
        }
        var easeFn = resolveCurve(k0.ease || 'easyEase');
        return lerpVal(k0.v, k1.v, easeFn(localU));
      }
    }
    return keyframes[lastIdx].v;
  }

  /**
   * Analytic numerical derivative (rate of change per second) of a keyframe track.
   * Drives velocity-accurate directional/shutter motion blur and radial aberration.
   */
  function trackVelocity(keyframes, t, durationS, dtSample) {
    var h = dtSample || 0.004;
    var vPrev = evalTrack(keyframes, t - h, durationS);
    var vNext = evalTrack(keyframes, t + h, durationS);
    if (Array.isArray(vPrev) && Array.isArray(vNext)) {
      var out = new Array(vPrev.length);
      for (var i = 0; i < vPrev.length; i++) out[i] = (vNext[i] - vPrev[i]) / (2 * h);
      return out;
    }
    return (vNext - vPrev) / (2 * h);
  }

  /**
   * Reference AkvzW2O0UeA: Bottom-anchored Pop-Up Overshoot Scale (0% -> 105% -> 100%).
   */
  function popOvershootTrack(t0, durationS, overshootPeak) {
    var peak = overshootPeak !== undefined ? overshootPeak : 1.06;
    var d = Math.max(0.08, durationS || 0.34);
    return [
      { t: t0, v: 0.0, ease: 'aeWhipOut' },
      { t: t0 + d * 0.68, v: peak, ease: 'smoothStop' },
      { t: t0 + d, v: 1.0 }
    ];
  }

  /**
   * Reference dHAx3HSVDLA: Discrete opacity flash strobe + subtle blur/invert pulse.
   */
  function flashStrobeEval(t, t0, durationS, cycles) {
    var dur = Math.max(0.12, durationS || 0.32);
    var nCycles = cycles || 3;
    var u = M.clamp01((t - t0) / dur);
    if (t < t0) return { active: false, cutoutOpacity: 0, flashPulse: 0, whiteFillMix: 0, scalePunch: 1.0 };
    if (t >= t0 + dur) return { active: false, cutoutOpacity: 1, flashPulse: 0, whiteFillMix: 0, scalePunch: 1.0 };

    var step = Math.floor(u * (nCycles * 2));
    var isOn = step % 2 === 0 ? 1.0 : 0.12;
    var pulse = Math.sin(u * Math.PI * nCycles) * 0.5 + 0.5;
    return {
      active: true,
      cutoutOpacity: isOn,
      flashPulse: pulse * (1 - u * 0.4),
      whiteFillMix: 1 - M.smoothstep(0.55, 1.0, u),
      scalePunch: 1.0 + 0.06 * Math.sin(u * Math.PI)
    };
  }

  /**
   * Reference camera-dolly-zoom (HyperFrames formula): d * tan(FOV/2) = const.
   */
  function solveDollyZoomFov(refDist, refFovDeg, curDist) {
    var halfRad = (refFovDeg * Math.PI) / 360;
    var targetPlaneHalfH = refDist * Math.tan(halfRad);
    var safeDist = Math.max(0.2, Math.abs(curDist));
    return (2 * Math.atan(targetPlaneHalfH / safeDist) * 180) / Math.PI;
  }

  /**
   * Convert camera focal length in mm (35mm full-frame 24mm vertical or 36mm horizontal) to vertical FOV.
   */
  function focalMmToFovDeg(focalMm, aspect) {
    var mm = Math.max(10, focalMm || 35);
    var sensorH = aspect < 1 ? 36.0 : 24.0;
    return (2 * Math.atan(sensorH / (2 * mm)) * 180) / Math.PI;
  }

  /**
   * Evaluate synchronized 3D camera + optical DoF state from declarative JSON spec.
   */
  function resolveCameraState(cameraSpec, t, durationS, aspect) {
    var s = cameraSpec || {};
    var dur = durationS || 4.0;
    var pos = s.positionTrack ? evalTrack(s.positionTrack, t, dur) : (s.position || [0, 0, 5.0]);
    var target = s.targetTrack ? evalTrack(s.targetTrack, t, dur) : (s.target || [0, 0, 0]);
    var rollDeg = s.rollTrack ? evalTrack(s.rollTrack, t, dur) : (s.rollDeg || 0);
    var focusDist = s.focusDistanceTrack ? evalTrack(s.focusDistanceTrack, t, dur) : (s.focusDistance || Math.hypot(pos[0] - target[0], pos[1] - target[1], pos[2] - target[2]));
    var aperturePx = s.apertureTrack ? evalTrack(s.apertureTrack, t, dur) : (s.aperturePx !== undefined ? s.aperturePx : 48.0);

    var baseFov = s.focalLengthMm ? focalMmToFovDeg(s.focalLengthMm, aspect || (9 / 16)) : (s.fovDeg || 48);
    var fovDeg = s.fovTrack ? evalTrack(s.fovTrack, t, dur) : baseFov;
    if (s.dollyZoom && s.dollyRefDist) {
      var d = Math.hypot(pos[0] - target[0], pos[1] - target[1], pos[2] - target[2]);
      fovDeg = solveDollyZoomFov(s.dollyRefDist, baseFov, d);
    }

    var speedVec = s.positionTrack ? trackVelocity(s.positionTrack, t, dur) : [0, 0, 0];
    var speedMag = Math.hypot(speedVec[0], speedVec[1], speedVec[2]);

    return {
      position: pos,
      target: target,
      rollDeg: rollDeg,
      fovDeg: fovDeg,
      focusDistance: focusDist,
      aperturePx: aperturePx,
      speedVec: speedVec,
      speedMag: speedMag
    };
  }

  /**
   * Project 3D world coordinate to CSS screen pixel space matching PerspectiveCamera lookAt + roll.
   * Ensures synced DOM/SVG text aligns pixel-perfect with Three.js meshes under the same camState.
   */
  function projectWorldToScreen(point3D, camState, width, height) {
    var px = point3D[0] - camState.position[0];
    var py = point3D[1] - camState.position[1];
    var pz = point3D[2] - camState.position[2];

    var fx = camState.target[0] - camState.position[0];
    var fy = camState.target[1] - camState.position[1];
    var fz = camState.target[2] - camState.position[2];
    var flen = Math.hypot(fx, fy, fz) || 1;
    fx /= flen; fy /= flen; fz /= flen;

    // Right = normalize(forward x worldUp(0,1,0))
    var rx = -fz;
    var ry = 0;
    var rz = fx;
    var rlen = Math.hypot(rx, ry, rz) || 1;
    rx /= rlen; ry /= rlen; rz /= rlen;

    // CamUp = right x forward
    var ux = ry * fz - rz * fy;
    var uy = rz * fx - rx * fz;
    var uz = rx * fy - ry * fx;

    var vx = px * rx + py * ry + pz * rz;
    var vy = px * ux + py * uy + pz * uz;
    var vz = px * fx + py * fy + pz * fz;

    if (camState.rollDeg) {
      var rad = (-camState.rollDeg * Math.PI) / 180;
      var c = Math.cos(rad);
      var sn = Math.sin(rad);
      var rvx = vx * c - vy * sn;
      var rvy = vx * sn + vy * c;
      vx = rvx;
      vy = rvy;
    }

    var safeZ = Math.max(0.12, vz);
    var fovRad = (camState.fovDeg * Math.PI) / 180;
    var focalPx = (height * 0.5) / Math.tan(fovRad * 0.5);

    var screenX = width * 0.5 + (vx / safeZ) * focalPx;
    var screenY = height * 0.5 - (vy / safeZ) * focalPx;
    var scale = focalPx / (safeZ * 100);

    var distFromFocus = Math.abs(vz - camState.focusDistance);
    var dofBlurPx = M.clamp01(distFromFocus / Math.max(0.8, 3.8)) * (camState.aperturePx / 7.5);
    var behindCamera = vz <= 0.18;

    return {
      x: screenX,
      y: screenY,
      viewDepth: vz,
      scale: scale,
      dofBlurPx: dofBlurPx,
      visible: !behindCamera,
      nearFade: behindCamera ? 0 : M.smoothstep(0.25, 0.9, vz)
    };
  }

  /**
   * Reference xCueXSWn-pk / ZcmcHeWWAuI: Distribute individual words along 3D spiral in XYZ space.
   * Never stacks words flat on a single Z depth.
   */
  function buildSpiralWordLayout(tokens, opts) {
    var o = opts || {};
    var radiusX = o.radiusX !== undefined ? o.radiusX : 1.35;
    var radiusY = o.radiusY !== undefined ? o.radiusY : 1.55;
    var startZ = o.startZ !== undefined ? o.startZ : 1.8;
    var stepZ = o.stepZ !== undefined ? o.stepZ : -0.68;
    var startAngle = o.startAngleRad !== undefined ? o.startAngleRad : -Math.PI * 0.72;
    var angleStep = o.angleStepRad !== undefined ? o.angleStepRad : 0.62;

    var out = [];
    for (var i = 0; i < tokens.length; i++) {
      var item = typeof tokens[i] === 'string' ? { text: tokens[i] } : tokens[i];
      var a = startAngle + i * angleStep;
      var x = (item.xOffset || 0) + Math.cos(a) * radiusX * (0.55 + 0.45 * (i / Math.max(1, tokens.length - 1)));
      var y = (item.yOffset || 0) + ((tokens.length - 1) * 0.5 - i) * 0.68 + Math.sin(a) * (radiusY * 0.16);
      var z = startZ + i * stepZ;
      out.push({
        text: item.text,
        role: item.role || 'hero',
        pos: [x, y, z],
        rotYDeg: (item.rotYDeg !== undefined ? item.rotYDeg : Math.sin(a) * 14),
        rotZDeg: (item.rotZDeg !== undefined ? item.rotZDeg : Math.cos(a) * -6),
        appearAt: item.appearAt !== undefined ? item.appearAt : i * 0.14
      });
    }
    return out;
  }

  /**
   * Composable Content Adapters for adapting the 4-axis rig cleanly across future formats.
   */
  var CONTENT_PRESETS = {
    talking_head_depth: {
      camera: { focalLengthMm: 35, aperturePx: 54, positionEase: 'aeWhipOut', backgroundParallaxZ: -2.4, backgroundScale: 1.24 },
      textMode: 'spiral_mixed_voice',
      occlusionTier: 'hook_burst_matte',
      transitionIn: 'flash_cutout_strobe',
      transitionOut: 'motion_tile_whip'
    },
    product_3d_orbit: {
      camera: { focalLengthMm: 50, aperturePx: 42, positionEase: 'easyEase', orbitDegPerSec: 36 },
      textMode: 'extruded_cylinder_ring',
      occlusionTier: 'popup_clean_plate',
      transitionIn: 'popup_anchor_scale',
      transitionOut: 'optical_radial_match'
    },
    mograph_editorial: {
      camera: { focalLengthMm: 35, aperturePx: 68, dollyZoom: true, positionEase: 'aeWhipOut' },
      textMode: 'spatial_3d_plus_glow_nib',
      occlusionTier: 'none',
      transitionIn: 'smooth_mask_reveal',
      transitionOut: 'motion_tile_whip'
    },
    montage_flash_edit: {
      camera: { focalLengthMm: 28, aperturePx: 32, rollPunchDeg: 8, positionEase: 'aeWhipInOut' },
      textMode: 'rolling_cylinder_or_ghost',
      occlusionTier: 'flash_cutout_burst',
      transitionIn: 'flash_cutout_strobe',
      transitionOut: 'optical_radial_match'
    }
  };

  /**
   * Compile a declarative scene spec into a WeftCut Multi-Track Sandwich Layer Plan.
   */
  function toWeftCutLayerPlan(sceneSpec) {
    var spec = sceneSpec || {};
    var layers = [
      {
        trackRole: 'background_plate',
        zOrder: 1,
        zParallaxDepth: spec.backgroundParallaxZ !== undefined ? spec.backgroundParallaxZ : -2.4,
        scaleCompensation: spec.backgroundScale !== undefined ? spec.backgroundScale : 1.24,
        purpose: '3D pushed background footage for camera parallax'
      },
      {
        trackRole: 'mid_3d_typography',
        zOrder: 2,
        motif: spec.motifName || 'kinetic-3d-spatial',
        blendMode: 'normal',
        purpose: '3D orbital ring, extruded text, or Mixed-Voice depth planes behind foreground occluder'
      }
    ];
    if (spec.foregroundCutout) {
      layers.push({
        trackRole: 'foreground_occluder',
        zOrder: 3,
        alphaMatteSource: spec.foregroundCutout,
        castShadow: true,
        anchor: spec.anchor || [0.5, 1.0],
        purpose: 'Rotoscoped foreground subject sandwiching 3D elements + contact shadow'
      });
    }
    if (spec.transitionAdjustment) {
      layers.push({
        trackRole: 'adjustment_seam_bridge',
        zOrder: 4,
        effect: spec.transitionAdjustment,
        purpose: 'Seam-straddling Motion Tile whip, Flash Cutout strobe, or Radial Optical Match'
      });
    }
    return layers;
  }

  return {
    SPEED_GRAPHS: SPEED_GRAPHS,
    resolveCurve: resolveCurve,
    evalTrack: evalTrack,
    trackVelocity: trackVelocity,
    popOvershootTrack: popOvershootTrack,
    flashStrobeEval: flashStrobeEval,
    solveDollyZoomFov: solveDollyZoomFov,
    focalMmToFovDeg: focalMmToFovDeg,
    resolveCameraState: resolveCameraState,
    projectWorldToScreen: projectWorldToScreen,
    buildSpiralWordLayout: buildSpiralWordLayout,
    CONTENT_PRESETS: CONTENT_PRESETS,
    toWeftCutLayerPlan: toWeftCutLayerPlan
  };
}));
