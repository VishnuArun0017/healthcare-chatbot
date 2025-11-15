'use client';

import Link from 'next/link';
import LightRays from './LightRays';

export default function HeroSection() {
  return (
    <section className="relative mx-auto flex w-full max-w-6xl flex-col gap-8 px-4 py-12 sm:gap-10 sm:px-6 sm:py-16 md:gap-12 md:px-8 lg:flex-row lg:items-center lg:gap-16 lg:px-10 lg:py-24 overflow-hidden">
      {/* LightRays Animation Background - covers entire section */}
      <div className="absolute inset-0 z-0">
        <LightRays
          raysOrigin="top-center"
          raysColor="#00ffff"
          raysSpeed={1.5}
          lightSpread={0.8}
          rayLength={1.2}
          followMouse={true}
          mouseInfluence={0.1}
          noiseAmount={0.1}
          distortion={0.05}
        />
      </div>
      
      {/* Content with relative z-index to appear above animation */}
      <div className="relative z-10 flex-1 space-y-6 sm:space-y-8">
        <div className="inline-flex items-center gap-1.5 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1.5 text-xs font-semibold text-emerald-200 shadow-[0_12px_35px_rgba(16,185,129,0.25)] sm:gap-2 sm:px-4 sm:py-2 sm:text-sm">
          <span className="inline-flex h-2 w-2 animate-pulse rounded-full bg-emerald-300 sm:h-2.5 sm:w-2.5" aria-hidden />
          Always-on Care Navigation
        </div>
        <div className="space-y-4 sm:space-y-5">
          <h1 className="text-2xl font-semibold text-white sm:text-3xl md:text-4xl lg:text-5xl xl:text-6xl">
            One-click clarity for complex health journeys.
          </h1>
          <p className="max-w-2xl text-sm leading-relaxed text-slate-200 sm:text-base md:text-lg">
            From symptom triage to warm hand-offs, Health Companion blends compassionate dialogue with
            clinical guardrails. Discover a canvas where glowing analytics, guided workflows, and real-world
            care converge in seconds.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3 sm:gap-4">
          <Link
            href="/auth"
            className="inline-flex items-center gap-2 rounded-full bg-gradient-to-br from-emerald-500 via-green-500 to-teal-500 px-5 py-2.5 text-xs font-semibold text-white shadow-[0_22px_45px_rgba(16,185,129,0.35)] transition hover:scale-[1.04] sm:px-6 sm:py-3 sm:text-sm"
          >
            Get Started
          </Link>
          <Link
            href="#insights"
            className="inline-flex items-center gap-2 rounded-full border border-white/10 px-5 py-2.5 text-xs font-semibold text-slate-100 transition hover:border-white/25 hover:text-white sm:px-6 sm:py-3 sm:text-sm"
          >
            Explore Insights
          </Link>
        </div>
      </div>
      <div className="relative z-10 flex-1 rounded-2xl border border-white/10 bg-white/5 shadow-[0_30px_90px_rgba(15,23,42,0.55)] backdrop-blur-xl overflow-hidden sm:rounded-3xl md:rounded-[32px]">
        <div className="h-full flex flex-col p-4 space-y-4 sm:p-5 sm:space-y-5 md:p-6 md:space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <p className="text-[0.65rem] font-semibold uppercase tracking-[0.32em] text-emerald-200/90 sm:text-xs">
              Live safety pulse
            </p>
            <span className="inline-flex items-center gap-1.5 text-[0.65rem] text-slate-200 sm:gap-2 sm:text-xs">
              <span className="inline-flex h-1.5 w-1.5 animate-ping rounded-full bg-emerald-300 sm:h-2 sm:w-2" aria-hidden />
              Monitoring
            </span>
          </div>

          {/* Guardrails Card */}
          <div className="rounded-2xl border border-white/10 bg-white/10 p-4 text-slate-100 shadow-inner shadow-emerald-500/10 sm:rounded-3xl sm:p-5 md:p-6">
            <p className="text-[0.65rem] uppercase tracking-[0.32em] text-emerald-100/80 sm:text-xs">Guardrails</p>
            <h3 className="mt-1.5 text-lg font-semibold text-white sm:mt-2 sm:text-xl md:text-2xl">Red-flag intercept</h3>
            <p className="mt-2 text-xs leading-relaxed text-slate-100/70 sm:mt-3 sm:text-sm">
              98% of emergencies flagged before hand-off. Visualize trending symptom signals and confidence
              scores to keep every conversation safe.
            </p>
            <div className="mt-4 sm:mt-6">
              <div className="flex items-end gap-2 sm:gap-3">
                {[65, 82, 74, 91].map((value, index) => (
                  <div key={index} className="flex flex-1 flex-col items-center gap-1.5 sm:gap-2">
                    <div className="flex w-2.5 rounded-full bg-emerald-400/30 sm:w-3">
                      <div
                        aria-hidden
                        className="mx-auto w-full rounded-full bg-gradient-to-b from-emerald-200 to-emerald-500"
                        style={{ height: `${value}%` }}
                      />
                    </div>
                    <span className="text-[0.55rem] font-semibold uppercase tracking-[0.32em] text-emerald-200/80 sm:text-[0.6rem]">
                      wk{index + 1}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Care Loops Card */}
          <div className="rounded-2xl border border-white/10 bg-white/10 p-4 text-slate-100 shadow-inner shadow-emerald-500/10 sm:rounded-3xl sm:p-5 md:p-6">
            <p className="text-[0.65rem] uppercase tracking-[0.32em] text-teal-200/80 sm:text-xs">Care loops</p>
            <h3 className="mt-1.5 text-base font-semibold text-white sm:mt-2 sm:text-lg md:text-xl">Return visit readiness</h3>
            <p className="mt-2 text-xs leading-relaxed text-slate-100/70 sm:mt-3 sm:text-sm">
              Track adherence, surface nudge moments, and hand off escalations to clinical teams with
              complete context.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

