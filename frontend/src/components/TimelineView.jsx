import React, { useState, useRef, useEffect } from "react";
import { Terminal, Activity, Box, GitCommit, Search, ChevronDown, ChevronUp, SlidersHorizontal } from "lucide-react";

export default function TimelineView({ events }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterSources, setFilterSources] = useState({
    loki: true,
    prometheus: true,
    kubernetes: true,
    github: true,
  });
  const [expandedEvents, setExpandedEvents] = useState({});

  const scrollRef = useRef(null);
  const [canScrollUp, setCanScrollUp] = useState(false);
  const [canScrollDown, setCanScrollDown] = useState(false);

  const checkScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    setCanScrollUp(el.scrollTop > 5);
    setCanScrollDown(el.scrollHeight - el.scrollTop - el.clientHeight > 5);
  };

  useEffect(() => {
    checkScroll();
    // Attach event listeners
    const el = scrollRef.current;
    if (el) {
      el.addEventListener("scroll", checkScroll);
      window.addEventListener("resize", checkScroll);
    }
    return () => {
      if (el) {
        el.removeEventListener("scroll", checkScroll);
      }
      window.removeEventListener("resize", checkScroll);
    };
  }, [events, searchTerm, filterSources]);

  const toggleSource = (source) => {
    setFilterSources((prev) => ({
      ...prev,
      [source]: !prev[source],
    }));
  };

  const toggleExpand = (index) => {
    setExpandedEvents((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  const getSourceIcon = (sourceType) => {
    switch (sourceType.toLowerCase()) {
      case "prometheus":
        return <Activity className="w-4 h-4 text-[#3b82f6]" />;
      case "loki":
        return <Terminal className="w-4 h-4 text-[#8b5cf6]" />;
      case "kubernetes":
        return <Box className="w-4 h-4 text-[#f59e0b]" />;
      case "github":
        return <GitCommit className="w-4 h-4 text-[#14b8a6]" />;
      default:
        return <Terminal className="w-4 h-4 text-gray-400" />;
    }
  };

  const getSourceBadgeClass = (sourceType) => {
    switch (sourceType.toLowerCase()) {
      case "prometheus":
        return "bg-blue-500/10 text-blue-400 border-blue-500/20";
      case "loki":
        return "bg-purple-500/10 text-purple-400 border-purple-500/20";
      case "kubernetes":
        return "bg-amber-500/10 text-amber-400 border-amber-500/20";
      case "github":
        return "bg-teal-500/10 text-teal-400 border-teal-500/20";
      default:
        return "bg-gray-500/10 text-gray-400 border-gray-500/20";
    }
  };

  const filteredEvents = (events || []).filter((e) => {
    const matchesSource = filterSources[e.source_type.toLowerCase()] !== false;
    const matchesSearch =
      e.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.source_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (e.event_type && e.event_type.toLowerCase().includes(searchTerm.toLowerCase()));
    return matchesSource && matchesSearch;
  });

  const formatTime = (isoString) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-900/40 border border-white/5 rounded-2xl overflow-hidden backdrop-blur-md">
      {/* Header & Filter Controls */}
      <div className="p-4 border-b border-white/5 bg-slate-950/20">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-3">
          <h3 className="font-display font-semibold text-lg text-white flex items-center gap-2">
            <SlidersHorizontal className="w-4 h-4 text-purple-400" />
            Evidence Timeline
          </h3>
          
          {/* Search Input */}
          <div className="relative flex-1 md:max-w-xs">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-500" />
            <input
              type="text"
              placeholder="Filter timeline..."
              className="w-full bg-slate-950/40 border border-white/10 rounded-lg py-1.5 pl-9 pr-4 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-purple-500/50 transition-colors"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        {/* Source Toggle Pills */}
        <div className="flex flex-wrap gap-2">
          {Object.keys(filterSources).map((src) => (
            <button
              key={src}
              onClick={() => toggleSource(src)}
              className={`px-3 py-1 rounded-full text-xs border transition-all flex items-center gap-1.5 ${
                filterSources[src]
                  ? "bg-slate-800 text-white border-white/10"
                  : "bg-slate-950/40 text-gray-500 border-transparent opacity-60"
              }`}
            >
              {getSourceIcon(src)}
              <span className="capitalize">{src === "kubernetes" ? "K8s" : src}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Scrollable Timeline Area */}
      <div className="relative flex-1 min-h-0">
        {/* Scroll Shadows */}
        <div 
          className={`absolute top-0 left-0 right-0 h-6 bg-gradient-to-b from-slate-900 to-transparent pointer-events-none z-10 transition-opacity duration-200 ${
            canScrollUp ? "opacity-100" : "opacity-0"
          }`} 
        />
        <div 
          className={`absolute bottom-0 left-0 right-0 h-6 bg-gradient-to-t from-slate-900 to-transparent pointer-events-none z-10 transition-opacity duration-200 ${
            canScrollDown ? "opacity-100" : "opacity-0"
          }`} 
        />

        <div
          ref={scrollRef}
          className="h-full overflow-y-auto px-4 py-3 space-y-4 scroller"
        >
          {filteredEvents.length === 0 ? (
            <div className="text-center py-10 text-gray-500 text-sm">
              No events match the active filters
            </div>
          ) : (
            filteredEvents.map((event, idx) => {
              const isExpanded = expandedEvents[idx];
              return (
                <div key={idx} className="relative pl-6 pb-2 border-l border-white/10 last:pb-0">
                  {/* Timeline dot */}
                  <div className="absolute -left-[9px] top-1.5 w-4.5 h-4.5 rounded-full bg-slate-900 border-2 border-slate-700 flex items-center justify-center">
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-400"></span>
                  </div>

                  {/* Card Content */}
                  <div className="glass-card !p-3.5 flex flex-col gap-2">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-semibold tracking-wider border uppercase ${getSourceBadgeClass(event.source_type)}`}>
                          {event.source_type}
                        </span>
                        <span className="text-gray-500 text-[10px]">
                          {formatTime(event.timestamp)}
                        </span>
                      </div>
                      
                      {event.metadata && Object.keys(event.metadata).length > 0 && (
                        <button
                          onClick={() => toggleExpand(idx)}
                          className="text-gray-400 hover:text-white p-0.5 rounded transition-colors"
                        >
                          {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                        </button>
                      )}
                    </div>

                    <p className="text-xs text-gray-200 leading-relaxed font-mono whitespace-pre-wrap">
                      {event.description}
                    </p>

                    {/* Expandable JSON Metadata Drawer */}
                    {isExpanded && event.metadata && (
                      <div className="mt-2 bg-black/40 border border-white/5 rounded-lg p-2.5 font-mono text-[10px] text-teal-400 overflow-x-auto">
                        <pre>{JSON.stringify(event.metadata, null, 2)}</pre>
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
