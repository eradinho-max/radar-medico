"use client";

import type { CSSProperties } from "react";

type Props = {
  total: number;
  label: string;
  official: number;
  auxiliary: number;
};

const points = [
  { id: "AM", x: 168, y: 126, delay: "0s" },
  { id: "PA", x: 274, y: 120, delay: ".7s" },
  { id: "CE", x: 365, y: 160, delay: "1.4s" },
  { id: "BA", x: 332, y: 236, delay: "2.1s" },
  { id: "GO", x: 262, y: 244, delay: "2.8s" },
  { id: "MG", x: 316, y: 292, delay: "3.5s" },
  { id: "SP", x: 280, y: 328, delay: "4.2s" },
  { id: "PR", x: 260, y: 361, delay: "4.9s" },
  { id: "RS", x: 232, y: 407, delay: "5.6s" },
];

export default function BrazilRadar({ total, label, official, auxiliary }: Props) {
  return (
    <div className="brazilRadarCard" aria-hidden="true">
      <div className="brazilRadarTop">
        <div>
          <span className="miniEyebrow">BUSCA NACIONAL</span>
          <strong>Monitoramento em tempo real</strong>
        </div>
        <span className="scanStatus"><i /> ativo</span>
      </div>

      <div className="brazilStage">
        <div className="radarAura" />
        <div className="radarSweepBrazil" />
        <svg className="brazilMapSvg" viewBox="0 0 500 470">
          <defs>
            <linearGradient id="brFill" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#263547" />
              <stop offset="100%" stopColor="#101923" />
            </linearGradient>
            <filter id="glow">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          <path
            className="countryShape"
            d="M132 41 L196 30 231 48 282 45 312 69 351 73 371 104 407 126 394 154 422 177 400 205 409 237 382 260 377 297 351 318 337 350 309 367 296 399 263 431 239 416 224 382 201 362 183 329 158 313 149 278 126 252 133 220 111 195 121 166 101 141 114 105 102 76 132 41 Z"
          />

          <g className="stateLines">
            <path d="M119 104 L183 112 215 84 282 82 346 105" />
            <path d="M126 154 L190 151 235 126 294 132 386 147" />
            <path d="M133 205 L196 195 249 178 314 183 403 192" />
            <path d="M145 257 L201 244 257 229 328 238 383 258" />
            <path d="M159 311 L220 291 277 281 348 300" />
            <path d="M191 357 L246 333 307 342" />
            <path d="M223 384 L276 367 301 397" />
            <path d="M182 112 L190 195 201 244 220 291 246 333" />
            <path d="M236 126 L249 178 257 229 277 281 307 342" />
            <path d="M294 132 L314 183 328 238 348 300" />
            <path d="M346 105 L386 147 403 192 383 258" />
          </g>

          {points.map((point) => (
            <g
              key={point.id}
              className="scanPoint"
              style={{ "--delay": point.delay } as CSSProperties}
              transform={`translate(${point.x} ${point.y})`}
            >
              <circle className="pointHalo" r="12" />
              <circle className="pointCore" r="4" filter="url(#glow)" />
            </g>
          ))}
        </svg>

        <div className="scanLegend">
          <span><i className="legendRed" /> varredura ativa</span>
          <span><i className="legendGreen" /> oportunidade validada</span>
        </div>
      </div>

      <div className="metrics premiumMetrics">
        <div>
          <strong>{total}</strong>
          <span>{label}</span>
        </div>
        <div>
          <strong>{official}</strong>
          <span>fontes oficiais</span>
        </div>
        <div>
          <strong>{auxiliary}</strong>
          <span>descobertas</span>
        </div>
      </div>
    </div>
  );
}
