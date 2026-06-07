"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Activity,
  Eye,
  ShieldCheck,
  Layers,
  Server,
  GitBranch,
  Github,
  PlayCircle
} from "lucide-react";

import "./landing.css";

const APP_URL = "/dashboard";
const GITHUB_URL = "https://github.com/Pavilion-devs/halo";
const DEMO_URL = "https://youtu.be/nW7aeeBrIZQ";

export default function LandingPage() {
  const footerTextRef = useRef<HTMLHeadingElement>(null);

  // Scroll reveal
  useEffect(() => {
    const revealElements = document.querySelectorAll(".reveal");
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) entry.target.classList.add("active");
        });
      },
      { threshold: 0.1, rootMargin: "0px 0px -50px 0px" }
    );
    revealElements.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  // Footer parallax
  useEffect(() => {
    const handleScroll = () => {
      if (footerTextRef.current) {
        const rect = footerTextRef.current.getBoundingClientRect();
        const windowHeight = window.innerHeight;
        if (rect.top < windowHeight) {
          const move = (windowHeight - rect.top) * 0.1;
          footerTextRef.current.style.transform = `translateX(-${move}px)`;
        }
      }
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className="halo-landing">
      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex justify-between items-center px-6 py-4 md:px-12 md:py-5 w-full max-w-[1800px] mx-auto bg-[#fdfdfc]/80 backdrop-blur-md transition-all duration-300 border-b border-transparent">
        <Link
          href="/"
          className="text-xl font-semibold tracking-tight cursor-pointer hover:opacity-70 transition-opacity"
        >
          Ha<span className="text-indigo-500">lo</span>
        </Link>
        <div className="flex items-center gap-6 md:gap-8">
          <div className="hidden md:flex gap-6 text-sm font-medium text-neutral-600">
            <a href="#how-it-works" className="hover:text-black transition-colors">
              How it works
            </a>
            <Link href="/docs" className="hover:text-black transition-colors">
              Docs
            </Link>
            <a
              href={DEMO_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-black transition-colors"
            >
              Demo
            </a>
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-black transition-colors"
            >
              GitHub
            </a>
          </div>
          <Link
            href={APP_URL}
            className="flex items-center gap-2 pl-5 pr-5 py-2.5 bg-neutral-900 text-white rounded-full text-sm font-semibold hover:bg-neutral-800 transition-all duration-300 shadow-lg shadow-neutral-900/10"
          >
            Launch the war room
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </nav>

      <main className="md:px-8 w-full max-w-[1800px] mt-24 mr-auto ml-auto pr-4 pb-20 pl-4">
        {/* Hero */}
        <section className="pt-10 md:pt-20 pb-12 relative">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-end mb-12">
            <div className="lg:col-span-7 reveal active">
              <h1 className="md:text-7xl lg:text-8xl leading-[1.05] text-5xl font-semibold tracking-tighter">
                Resilient
                <br />
                incident
                <br />
                <span className="text-indigo-500">commander</span>
              </h1>
            </div>
            <div className="lg:col-span-5 flex flex-col items-start lg:items-end lg:pl-10 reveal delay-100 active">
              <p className="text-lg md:text-xl text-neutral-600 mb-8 max-w-sm lg:text-right font-medium">
                Halo investigates a live product, holds risky fixes behind a human, and keeps going when models rate-limit or tools fail. It degrades instead of dying.
              </p>
              <Link
                href={APP_URL}
                className="group flex items-center gap-3 pl-6 pr-6 py-3.5 bg-neutral-900 text-white rounded-full hover:bg-neutral-800 transition-all duration-300 shadow-xl shadow-neutral-900/10 hover:shadow-neutral-900/20 hover:-translate-y-1"
              >
                <span className="text-sm font-semibold">Launch the war room</span>
                <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center group-hover:bg-white/30 transition-colors">
                  <ArrowRight className="w-4 h-4" />
                </div>
              </Link>
            </div>
          </div>

          {/* Hero Card */}
          <div className="reveal delay-200 w-full h-[400px] md:h-[550px] rounded-[2rem] md:rounded-[3rem] overflow-hidden relative border border-neutral-200 shadow-sm active">
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-50 via-white to-neutral-50" />
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_40%,rgba(99,102,241,0.08),transparent_60%)]" />

            {/* Floating card */}
            <div className="absolute bottom-8 left-8 md:bottom-12 md:left-12 bg-white/95 backdrop-blur-xl p-6 rounded-2xl shadow-2xl max-w-sm w-full hidden md:block border border-white/50">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <p className="text-[10px] uppercase tracking-wider text-neutral-500 font-semibold mb-1">
                    Live incident
                  </p>
                  <h4 className="text-sm font-bold text-neutral-900">
                    Jaguar worker offline after deploy
                  </h4>
                </div>
                <div className="bg-emerald-100 text-emerald-700 border border-emerald-200 text-[10px] px-2 py-0.5 rounded-full font-semibold flex items-center gap-1">
                  <span className="w-1 h-1 rounded-full bg-emerald-600 animate-pulse" />
                  Production
                </div>
              </div>
              <div className="space-y-1.5">
                <div className="flex justify-between text-[11px] font-medium text-neutral-600">
                  <span>State checkpointed</span>
                  <span className="text-indigo-500">100%</span>
                </div>
                <div className="h-1.5 w-full bg-neutral-100 rounded-full overflow-hidden">
                  <div className="h-full bg-indigo-500 w-full rounded-full" />
                </div>
              </div>
            </div>

            {/* Approval badge */}
            <div className="absolute top-8 right-8 md:top-12 md:right-12 bg-white/95 backdrop-blur-xl px-5 py-3 rounded-xl shadow-lg border border-white/50 hidden md:flex items-center gap-3">
              <ShieldCheck className="w-5 h-5 text-indigo-500" />
              <div>
                <p className="text-xs font-semibold text-neutral-900">
                  Human approval gate
                </p>
                <p className="text-[10px] text-neutral-500">
                  No write runs without a person
                </p>
              </div>
            </div>

            {/* Center graphic */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="relative">
                <div className="w-32 h-32 md:w-48 md:h-48 rounded-full border-2 border-dashed border-indigo-200 animate-[spin_20s_linear_infinite] flex items-center justify-center">
                  <div className="w-20 h-20 md:w-28 md:h-28 rounded-full border border-indigo-300 flex items-center justify-center bg-white/50 backdrop-blur-sm">
                    <Activity className="w-8 h-8 md:w-12 md:h-12 text-indigo-500 stroke-[1.5]" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <div className="w-full h-px bg-gradient-to-r from-transparent via-neutral-200 to-transparent my-16 opacity-50" />

        {/* How It Works */}
        <section
          id="how-it-works"
          className="scroll-mt-28 rounded-[2rem] md:rounded-[3rem] bg-[#111111] text-white p-8 md:p-16 lg:p-24 overflow-hidden relative reveal"
        >
          <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-indigo-900/20 rounded-full blur-[100px] -translate-y-1/2 translate-x-1/2 pointer-events-none" />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 relative z-10">
            <div className="flex flex-col justify-center">
              <div className="mb-8 flex items-center gap-2 text-neutral-400 text-sm font-medium tracking-wide uppercase">
                <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" />
                How It Works
              </div>
              <h2 className="text-5xl md:text-7xl font-semibold tracking-tighter leading-tight mb-8">
                Detect.
                <span className="flex items-center gap-4 text-neutral-500">
                  <Eye className="w-12 h-12 md:w-16 md:h-16 stroke-[1.5]" />
                  Decide.
                </span>
                Verify.
              </h2>
              <p className="text-xl md:text-2xl text-neutral-400 max-w-md leading-relaxed">
                Halo pulls live evidence through MCP tools, diagnoses what&apos;s actually wrong, and holds any risky action for a human. Once approved, it executes — then re-checks the product to confirm the fix held.
              </p>
            </div>
            <div className="relative mt-8 lg:mt-0">
              <div className="bg-[#1A1A1A] border border-neutral-800 rounded-2xl p-6 md:p-8 shadow-2xl">
                <div className="space-y-6">
                  <div className="flex gap-4 items-start">
                    <div className="w-10 h-10 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 text-sm font-bold shrink-0">
                      1
                    </div>
                    <div>
                      <h4 className="font-semibold text-white mb-1">
                        Detect &amp; Diagnose
                      </h4>
                      <p className="text-neutral-500 text-sm">
                        Pulls live worker status, ingestion, deploys, and failures through Jaguar&apos;s MCP tools and works out the real root cause.
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-4 items-start">
                    <div className="w-10 h-10 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 text-sm font-bold shrink-0">
                      2
                    </div>
                    <div>
                      <h4 className="font-semibold text-white mb-1">
                        Decide with a human
                      </h4>
                      <p className="text-neutral-500 text-sm">
                        Prepares a recovery action — like a worker restart — but never touches production on its own. Every write waits for operator approval.
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-4 items-start">
                    <div className="w-10 h-10 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 text-sm font-bold shrink-0">
                      3
                    </div>
                    <div>
                      <h4 className="font-semibold text-white mb-1">
                        Execute &amp; Verify
                      </h4>
                      <p className="text-neutral-500 text-sm">
                        On approval it runs the action through the live ops path, then re-checks the product and reports whether the fix actually worked.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="mt-8 bg-[#222] rounded-xl p-6 border border-neutral-700">
                  <div className="flex justify-between text-xs font-medium text-neutral-500 mb-4">
                    <span className="text-white">Operating Modes</span>
                    <span>TrueFoundry + Bedrock</span>
                  </div>
                  <div className="text-2xl md:text-3xl font-mono-display text-white mb-2 text-center tracking-tight font-light">
                    NORMAL → DEGRADED → BLACKOUT
                  </div>
                  <div className="text-neutral-500 text-sm mb-6 text-center">
                    Degrades instead of dying when things break
                  </div>
                  <Link
                    href={APP_URL}
                    className="block w-full py-3.5 bg-white text-black text-sm font-bold rounded-full hover:bg-neutral-200 hover:scale-[1.02] active:scale-95 transition-all duration-300 shadow-[0_0_20px_rgba(255,255,255,0.1)] text-center"
                  >
                    Launch the war room
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>

        <div className="w-full h-px bg-neutral-200 my-20" />

        {/* Features */}
        <section className="py-12 md:py-24 relative reveal">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-16 gap-8">
            <div className="max-w-2xl">
              <div className="text-xs font-semibold tracking-widest text-neutral-500 uppercase mb-4">
                Features
              </div>
              <h2 className="md:text-5xl lg:text-6xl leading-[1.1] text-4xl font-semibold text-neutral-900 tracking-tighter">
                Built to stay standing when infrastructure doesn&apos;t.
              </h2>
            </div>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            <div className="relative bg-indigo-100 rounded-3xl p-8 flex flex-col min-h-[320px] hover:scale-[1.01] transition-transform duration-300">
              <div className="flex items-center gap-2 mb-2">
                <GitBranch className="w-5 h-5 text-indigo-700" />
                <span className="text-sm font-medium text-neutral-800">
                  Model Fallback
                </span>
              </div>
              <p className="text-neutral-600 text-sm mt-2 max-w-xs">
                Virtual models on AWS Bedrock fail over automatically. A rate-limit on the primary doesn&apos;t kill the run — it routes to a backup.
              </p>
              <div className="text-5xl md:text-6xl font-semibold text-black tracking-tighter mb-1 mt-auto">
                Zero
                <span className="text-sm font-sans font-medium tracking-normal align-middle opacity-60 ml-2">
                  CRASH ON RATE-LIMIT
                </span>
              </div>
            </div>
            <div className="bg-neutral-50 rounded-3xl p-8 flex flex-col min-h-[320px] hover:bg-neutral-100 transition-colors duration-300">
              <div className="flex items-center gap-2 mb-2">
                <ShieldCheck className="w-5 h-5 text-neutral-600" />
                <span className="text-sm font-medium text-neutral-600">
                  Human Approval Gate
                </span>
              </div>
              <p className="text-neutral-500 text-sm mt-2 max-w-xs">
                Read and write tools are split across two MCP servers. Anything that writes is isolated and never executes without a person.
              </p>
              <div className="text-5xl md:text-6xl font-semibold text-black tracking-tighter mb-1 mt-auto">
                Gated
                <span className="text-sm font-sans font-medium tracking-normal align-middle opacity-60 ml-2">
                  EVERY WRITE ACTION
                </span>
              </div>
            </div>
            <div className="bg-neutral-50 rounded-3xl p-8 flex flex-col min-h-[320px] hover:bg-neutral-100 transition-colors duration-300">
              <div className="flex items-center gap-2 mb-2">
                <Server className="w-5 h-5 text-neutral-600" />
                <span className="text-sm font-medium text-neutral-600">
                  Mode Ladder
                </span>
              </div>
              <p className="text-neutral-500 text-sm mt-2 max-w-xs">
                Under stress Halo steps down — normal, then a cheaper model with read-only tools, then blackout where it stops and hands off to a human.
              </p>
              <div className="text-5xl md:text-6xl font-semibold text-black tracking-tighter mb-1 mt-auto">
                Safe
                <span className="text-sm font-sans font-medium tracking-normal align-middle opacity-60 ml-2">
                  DEGRADATION
                </span>
              </div>
            </div>
          </div>
          <div className="bg-neutral-50 rounded-3xl p-8 flex flex-col min-h-[200px] hover:bg-neutral-100 transition-colors duration-300">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-5 h-5 text-neutral-600" />
              <span className="text-sm font-medium text-neutral-600">
                Full TrueFoundry Trace
              </span>
            </div>
            <p className="text-neutral-500 text-sm mt-2 max-w-lg">
              Every step leaves a trace — which model resolved, how many spans, which guardrails fired, and exactly which tools the agent called — surfaced right in the war room.
            </p>
            <div className="text-5xl md:text-6xl font-semibold text-black tracking-tighter mb-1 mt-auto">
              Verified
              <span className="text-sm font-sans font-medium tracking-normal align-middle opacity-60 ml-2">
                EVERY STEP
              </span>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="mb-20">
          <div className="relative w-full rounded-[2.5rem] bg-[#111111] overflow-hidden px-8 py-20 md:py-32 text-center reveal">
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-900/20 rounded-full blur-[120px] pointer-events-none" />
            <div className="relative z-10 max-w-3xl mx-auto flex flex-col items-center">
              <h2 className="text-5xl md:text-7xl lg:text-8xl font-semibold text-white tracking-tighter leading-none mb-8">
                Ready when
                <br />
                things break?
              </h2>
              <p className="text-neutral-400 text-lg md:text-xl mb-10 max-w-lg leading-relaxed">
                Watch Halo investigate a real incident, hold a fix behind approval, and tell you the truth about whether it actually worked.
              </p>
              <div className="flex flex-col md:flex-row items-center gap-4 w-full justify-center">
                <a
                  href={DEMO_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-10 py-4 bg-white text-black rounded-full text-base font-bold hover:bg-neutral-200 hover:scale-105 transition-all duration-300 shadow-[0_0_20px_rgba(255,255,255,0.15)] min-w-[200px]"
                >
                  Watch the demo
                </a>
                <a
                  href={GITHUB_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-10 py-4 bg-transparent border border-neutral-700 text-white rounded-full text-base font-semibold hover:border-white transition-all duration-300 min-w-[200px]"
                >
                  View on GitHub
                </a>
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <section className="mt-20 overflow-hidden border-t border-black pt-12 relative">
          <div className="w-full overflow-hidden py-10">
            <h1
              ref={footerTextRef}
              className="text-[15vw] leading-[0.8] uppercase whitespace-nowrap select-none transition-transform duration-75 will-change-transform font-bold text-black tracking-tighter"
              style={{ transform: "translateX(0)" }}
            >
              Halo
            </h1>
          </div>
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mt-8 gap-6 pb-12 reveal">
            <div className="flex gap-4">
              <a
                href={GITHUB_URL}
                target="_blank"
                rel="noopener noreferrer"
                aria-label="GitHub"
                className="w-12 h-12 bg-neutral-100 rounded-full flex items-center justify-center border border-neutral-200 hover:bg-neutral-200 transition-colors"
              >
                <Github className="w-5 h-5" />
              </a>
              <a
                href={DEMO_URL}
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Watch the demo"
                className="w-12 h-12 bg-neutral-100 rounded-full flex items-center justify-center border border-neutral-200 hover:bg-neutral-200 transition-colors"
              >
                <PlayCircle className="w-5 h-5" />
              </a>
            </div>
            <div className="text-sm font-medium text-neutral-500">
              Built for the TrueFoundry Resilient Agents hackathon
            </div>
            <div className="text-sm font-medium text-neutral-400">
              Powered by TrueFoundry AI Gateway + AWS Bedrock
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
