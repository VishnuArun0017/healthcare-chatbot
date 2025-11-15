'use client';

import { useEffect, useState, useRef } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { Linkedin, ArrowLeft } from 'lucide-react';
import clsx from 'clsx';

interface TeamMember {
  name: string;
  image: string;
  linkedinUrl: string;
  description: string;
}

const teamMembers: TeamMember[] = [
  {
    name: 'Vishnu A',
    image: '/Vishnu.png',
    linkedinUrl: 'https://linkedin.com/in/vishnu-a-webdevops',
    description: 'Energetic and innovative developer with a passion for creating impactful healthcare solutions. Brings fresh perspectives and technical excellence to every project.',
  },
  {
    name: 'Vishal D',
    image: '/Business photo Final.png',
    linkedinUrl: 'https://www.linkedin.com/in/vishal-d-079577290/',
    description: 'Dedicated and detail-oriented engineer committed to building robust systems. Combines technical expertise with a collaborative spirit to deliver exceptional results.',
  },
  {
    name: 'Tarun',
    image: '/tarun.jpeg',
    linkedinUrl: 'https://www.linkedin.com/in/tarun-thimmayan-9301b9290',
    description: 'Creative problem-solver with a strong foundation in software engineering. Passionate about leveraging technology to solve real-world healthcare challenges.',
  },
];

const commonQualification = 'Chennai Institute of Technology - Computer Science Engineering - 3rd year';

export default function TeamPage() {
  const [headerVisible, setHeaderVisible] = useState(false);
  const [visibleMembers, setVisibleMembers] = useState<Set<number>>(new Set());
  const memberRefs = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    // Animate header first
    const headerTimer = setTimeout(() => {
      setHeaderVisible(true);
    }, 100);

    return () => {
      clearTimeout(headerTimer);
    };
  }, []);

  useEffect(() => {
    const observers: IntersectionObserver[] = [];

    memberRefs.current.forEach((ref, index) => {
      if (!ref) return;

      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              setVisibleMembers((prev) => {
                const newSet = new Set(prev);
                newSet.add(index);
                return newSet;
              });
              // Once visible, we can stop observing
              observer.unobserve(ref);
            }
          });
        },
        {
          threshold: 0.2, // Trigger when 20% of the element is visible
          rootMargin: '0px 0px -100px 0px', // Trigger slightly before fully in view
        }
      );

      observer.observe(ref);
      observers.push(observer);
    });

    return () => {
      observers.forEach((observer) => observer.disconnect());
    };
  }, []);

  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-950 text-slate-100">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_15%_20%,rgba(16,185,129,0.25),transparent_55%),radial-gradient(circle_at_85%_15%,rgba(34,197,94,0.24),transparent_55%),linear-gradient(180deg,rgba(2,6,23,0.92),rgba(2,6,23,0.97))]" />
      
      <header
        className={clsx(
          'relative z-10 border-b border-white/5 bg-slate-950/60 backdrop-blur-xl transition-all duration-700',
          headerVisible
            ? 'opacity-100 translate-y-0'
            : 'opacity-0 -translate-y-4'
        )}
      >
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-4 sm:px-6 sm:py-5 md:py-6 lg:px-10">
          <Link
            href="/landing"
            className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-slate-900/70 px-3 py-1.5 text-xs font-semibold text-slate-200 transition-all hover:border-emerald-400/70 hover:text-emerald-200 hover:scale-105 sm:gap-2 sm:px-4 sm:py-2 sm:text-sm"
          >
            <ArrowLeft className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
            <span>Back</span>
          </Link>
          <div>
            <h1 className="text-lg font-semibold text-white sm:text-xl md:text-2xl">Meet Our Team</h1>
          </div>
          <div className="w-20" /> {/* Spacer for centering */}
        </div>
      </header>

      <main className="relative z-10 mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 sm:py-12 md:px-8 md:py-16 lg:px-10 lg:py-20">
        <div className="space-y-12 sm:space-y-16 md:space-y-20">
          {/* Animated background gradient for visual appeal */}
          <div className="pointer-events-none fixed inset-0 -z-0 opacity-30">
            <div className="absolute top-1/4 left-1/4 h-96 w-96 rounded-full bg-emerald-500/20 blur-3xl animate-pulse" style={{ animationDuration: '4s' }} />
            <div className="absolute top-1/2 right-1/4 h-96 w-96 rounded-full bg-teal-500/20 blur-3xl animate-pulse" style={{ animationDuration: '5s', animationDelay: '1s' }} />
            <div className="absolute bottom-1/4 left-1/2 h-96 w-96 rounded-full bg-green-500/20 blur-3xl animate-pulse" style={{ animationDuration: '6s', animationDelay: '2s' }} />
          </div>
          {teamMembers.map((member, index) => {
            const isVisible = visibleMembers.has(index);
            return (
              <div
                key={member.name}
                ref={(el) => {
                  memberRefs.current[index] = el;
                }}
                className="grid gap-6 md:grid-cols-2 md:gap-8 lg:gap-12"
              >
                {/* Left Side - Image, Name, LinkedIn */}
                <div
                  className={clsx(
                    'flex flex-col items-center gap-4 transition-all duration-700 ease-out sm:gap-6',
                    isVisible
                      ? 'opacity-100 translate-x-0 scale-100'
                      : 'opacity-0 -translate-x-12 scale-95'
                  )}
                  style={{ transitionDelay: isVisible ? '200ms' : '0ms' }}
                >
                <div className="relative h-48 w-48 overflow-hidden rounded-2xl border border-white/10 bg-slate-900/60 shadow-[0_25px_60px_rgba(16,185,129,0.25)] transition-all duration-500 hover:scale-105 hover:shadow-[0_35px_80px_rgba(16,185,129,0.4)] sm:h-56 sm:w-56 md:h-64 md:w-64 md:rounded-3xl">
                  <Image
                    src={member.image}
                    alt={member.name}
                    fill
                    className="object-cover transition-transform duration-500 hover:scale-110"
                    sizes="(max-width: 640px) 192px, (max-width: 768px) 224px, 256px"
                    priority={index === 0}
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-900/20 via-transparent to-transparent opacity-0 transition-opacity duration-300 hover:opacity-100" />
                </div>
                <div className="text-center">
                  <h2
                    className={clsx(
                      'text-xl font-semibold text-white transition-all duration-500 sm:text-2xl md:text-3xl',
                      isVisible
                        ? 'opacity-100 translate-y-0'
                        : 'opacity-0 translate-y-4'
                    )}
                    style={{ transitionDelay: isVisible ? '400ms' : '0ms' }}
                  >
                    {member.name}
                  </h2>
                  <a
                    href={member.linkedinUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={clsx(
                      'mt-3 inline-flex items-center gap-2 rounded-full border border-white/10 bg-slate-900/70 px-4 py-2 text-xs font-medium text-slate-200 transition-all duration-300 hover:border-emerald-400/60 hover:bg-emerald-500/10 hover:text-emerald-200 hover:scale-105 hover:shadow-[0_10px_30px_rgba(16,185,129,0.3)] sm:text-sm',
                      isVisible
                        ? 'opacity-100 translate-y-0'
                        : 'opacity-0 translate-y-4'
                    )}
                    style={{ transitionDelay: isVisible ? '500ms' : '0ms' }}
                  >
                    <Linkedin className="h-4 w-4 transition-transform duration-300 group-hover:scale-110" />
                    <span>LinkedIn</span>
                  </a>
                </div>
              </div>

              {/* Right Side - Qualification and Description */}
              <div
                className={clsx(
                  'flex flex-col justify-center gap-6 transition-all duration-700 ease-out sm:gap-8',
                  isVisible
                    ? 'opacity-100 translate-x-0 scale-100'
                    : 'opacity-0 translate-x-12 scale-95'
                )}
                style={{ transitionDelay: isVisible ? '600ms' : '0ms' }}
              >
                <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-5 shadow-[0_25px_60px_rgba(15,23,42,0.55)] backdrop-blur-xl transition-all duration-500 hover:border-emerald-400/30 hover:shadow-[0_35px_80px_rgba(16,185,129,0.25)] sm:rounded-3xl sm:p-6 md:p-8">
                  <div
                    className={clsx(
                      'mb-4 transition-all duration-500',
                      isVisible
                        ? 'opacity-100 translate-y-0'
                        : 'opacity-0 translate-y-4'
                    )}
                    style={{ transitionDelay: isVisible ? '700ms' : '0ms' }}
                  >
                    <p className="text-xs font-semibold uppercase tracking-[0.32em] text-emerald-300/80 sm:text-sm">
                      Qualification
                    </p>
                    <p className="mt-2 text-sm font-medium text-white sm:text-base md:text-lg">
                      {commonQualification}
                    </p>
                  </div>
                  <div
                    className={clsx(
                      'border-t border-white/10 pt-4 transition-all duration-500',
                      isVisible
                        ? 'opacity-100 translate-y-0'
                        : 'opacity-0 translate-y-4'
                    )}
                    style={{ transitionDelay: isVisible ? '800ms' : '0ms' }}
                  >
                    <p className="text-xs font-semibold uppercase tracking-[0.32em] text-emerald-300/80 sm:text-sm">
                      About
                    </p>
                    <p className="mt-3 text-sm leading-relaxed text-slate-200/80 sm:text-base">
                      {member.description}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          );
          })}
        </div>
      </main>
    </div>
  );
}

