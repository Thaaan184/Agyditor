import * as THREE from 'three';
import opentype from 'opentype.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { BokehPass } from 'three/examples/jsm/postprocessing/BokehPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/examples/jsm/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
import { Font } from 'three/examples/jsm/loaders/FontLoader.js';
import { TextGeometry } from 'three/examples/jsm/geometries/TextGeometry.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';

function parseTtfToFont(arrayBuffer) {
  const font = opentype.parse(arrayBuffer);
  const round = Math.round;
  const glyphs = {};
  const scale = 100000 / ((font.unitsPerEm || 2048) * 72);
  const glyphIndexMap = font.encoding.cmap.glyphIndexMap;
  const unicodes = Object.keys(glyphIndexMap);

  for (let i = 0; i < unicodes.length; i++) {
    const unicode = unicodes[i];
    const glyph = font.glyphs.glyphs[glyphIndexMap[unicode]];
    if (unicode !== undefined && glyph) {
      const token = {
        ha: round(glyph.advanceWidth * scale),
        x_min: round(glyph.xMin * scale),
        x_max: round(glyph.xMax * scale),
        o: ''
      };
      glyph.path.commands.forEach((command) => {
        const type = command.type.toLowerCase() === 'c' ? 'b' : command.type.toLowerCase();
        token.o += type + ' ';
        if (command.x !== undefined && command.y !== undefined) {
          token.o += round(command.x * scale) + ' ' + round(command.y * scale) + ' ';
        }
        if (command.x1 !== undefined && command.y1 !== undefined) {
          token.o += round(command.x1 * scale) + ' ' + round(command.y1 * scale) + ' ';
        }
        if (command.x2 !== undefined && command.y2 !== undefined) {
          token.o += round(command.x2 * scale) + ' ' + round(command.y2 * scale) + ' ';
        }
      });
      if (Array.isArray(glyph.unicodes) && glyph.unicodes.length > 0) {
        glyph.unicodes.forEach((u) => {
          glyphs[String.fromCodePoint(u)] = token;
        });
      } else {
        glyphs[String.fromCodePoint(glyph.unicode)] = token;
      }
    }
  }

  return new Font({
    glyphs,
    familyName: font.getEnglishName('fullName'),
    ascender: round(font.ascender * scale),
    descender: round(font.descender * scale),
    underlinePosition: font.tables.post.underlinePosition,
    underlineThickness: font.tables.post.underlineThickness,
    boundingBox: {
      xMin: font.tables.head.xMin,
      xMax: font.tables.head.xMax,
      yMin: font.tables.head.yMin,
      yMax: font.tables.head.yMax
    },
    resolution: 1000,
    original_font_information: font.tables.name
  });
}

globalThis.THREE = THREE;
globalThis.THREEX = {
  EffectComposer,
  RenderPass,
  BokehPass,
  UnrealBloomPass,
  ShaderPass,
  OutputPass,
  Font,
  TextGeometry,
  RoomEnvironment,
  parseTtfToFont,
  parseTtfOpenType: function (arrayBuffer) {
    return opentype.parse(arrayBuffer);
  }
};
