import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

export default function GraphExplorer({ graphData, rootCauseKeys }) {
  const svgRef = useRef(null);

  useEffect(() => {
    if (!graphData || !graphData.nodes || graphData.nodes.length === 0) return;

    const width = svgRef.current.clientWidth || 500;
    const height = 400;

    // Clear previous SVG contents
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    // Create a container group for zoom/pan support
    const g = svg.append("g");

    // Add zoom behavior
    svg.call(
      d3.zoom().on("zoom", (event) => {
        g.attr("transform", event.transform);
      })
    );

    // Deep copy data for D3 mutation
    const nodes = graphData.nodes.map((d) => ({ ...d }));
    const links = graphData.edges.map((d) => ({
      source: d.source,
      target: d.target,
      relationship: d.relationship,
    }));

    // Setup force simulation
    const simulation = d3
      .forceSimulation(nodes)
      .force("link", d3.forceLink(links).id((d) => d.id).distance(120))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(40));

    // Draw lines (edges)
    const link = g
      .append("g")
      .attr("stroke", "rgba(255,255,255,0.15)")
      .attr("stroke-width", 2)
      .selectAll("line")
      .data(links)
      .enter()
      .append("line");

    // Edge labels (optional but helpful)
    const linkText = g
      .append("g")
      .selectAll("text")
      .data(links)
      .enter()
      .append("text")
      .attr("font-size", "9px")
      .attr("fill", "var(--text-muted)")
      .attr("text-anchor", "middle")
      .text((d) => d.relationship || "calls");

    // Draw node groups
    const node = g
      .append("g")
      .selectAll("g")
      .data(nodes)
      .enter()
      .append("g")
      .attr("cursor", "grab")
      .call(
        d3
          .drag()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended)
      );

    // Node circles
    node
      .append("circle")
      .attr("r", 20)
      .attr("fill", (d) => {
        const name = d.id.toLowerCase();
        const isRoot = rootCauseKeys.some((k) => name.includes(k.toLowerCase()) || k.toLowerCase().includes(name));
        if (isRoot) return "rgba(239, 68, 68, 0.2)"; // glowing red
        
        switch (d.node_type) {
          case "database":
            return "rgba(245, 158, 11, 0.2)"; // orange
          case "cache":
            return "rgba(20, 184, 166, 0.2)"; // teal
          default:
            return "rgba(59, 130, 246, 0.2)"; // blue
        }
      })
      .attr("stroke", (d) => {
        const name = d.id.toLowerCase();
        const isRoot = rootCauseKeys.some((k) => name.includes(k.toLowerCase()) || k.toLowerCase().includes(name));
        if (isRoot) return "var(--status-failed)";
        
        switch (d.node_type) {
          case "database":
            return "var(--status-queued)";
          case "cache":
            return "var(--accent-teal)";
          default:
            return "var(--status-running)";
        }
      })
      .attr("stroke-width", (d) => {
        const name = d.id.toLowerCase();
        const isRoot = rootCauseKeys.some((k) => name.includes(k.toLowerCase()) || k.toLowerCase().includes(name));
        return isRoot ? 3 : 1.5;
      })
      .style("filter", (d) => {
        const name = d.id.toLowerCase();
        const isRoot = rootCauseKeys.some((k) => name.includes(k.toLowerCase()) || k.toLowerCase().includes(name));
        return isRoot ? "drop-shadow(0px 0px 8px rgba(239, 68, 68, 0.8))" : "none";
      });

    // Inner icon or dot for visual hierarchy
    node
      .append("circle")
      .attr("r", 5)
      .attr("fill", (d) => {
        const name = d.id.toLowerCase();
        const isRoot = rootCauseKeys.some((k) => name.includes(k.toLowerCase()) || k.toLowerCase().includes(name));
        if (isRoot) return "var(--status-failed)";
        
        switch (d.node_type) {
          case "database":
            return "var(--status-queued)";
          case "cache":
            return "var(--accent-teal)";
          default:
            return "var(--status-running)";
        }
      });

    // Node labels (texts)
    node
      .append("text")
      .attr("dy", 35)
      .attr("text-anchor", "middle")
      .attr("fill", "var(--text-primary)")
      .attr("font-size", "11px")
      .attr("font-family", "var(--font-sans)")
      .attr("font-weight", (d) => {
        const name = d.id.toLowerCase();
        const isRoot = rootCauseKeys.some((k) => name.includes(k.toLowerCase()) || k.toLowerCase().includes(name));
        return isRoot ? "700" : "500";
      })
      .text((d) => d.id);

    // Update positions on tick
    simulation.on("tick", () => {
      link
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y);

      linkText
        .attr("x", (d) => (d.source.x + d.target.x) / 2)
        .attr("y", (d) => (d.source.y + d.target.y) / 2 - 5);

      node.attr("transform", (d) => `translate(${d.x},${d.y})`);
    });

    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    return () => {
      simulation.stop();
    };
  }, [graphData, rootCauseKeys]);

  return (
    <div className="relative w-full h-[400px] bg-black/20 rounded-xl overflow-hidden border border-white/5">
      <div className="absolute top-4 left-4 z-10 flex items-center space-x-4 text-xs text-secondary bg-slate-900/60 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/5">
        <span className="flex items-center"><span className="w-2.5 h-2.5 rounded-full bg-[#ef4444] mr-1.5 shadow-[0_0_6px_rgba(239,68,68,0.8)]"></span>Root Cause</span>
        <span className="flex items-center"><span className="w-2.5 h-2.5 rounded-full bg-[#f59e0b] mr-1.5"></span>Database</span>
        <span className="flex items-center"><span className="w-2.5 h-2.5 rounded-full bg-[#14b8a6] mr-1.5"></span>Cache</span>
        <span className="flex items-center"><span className="w-2.5 h-2.5 rounded-full bg-[#3b82f6] mr-1.5"></span>Service</span>
      </div>
      <svg ref={svgRef} className="w-full h-full" />
    </div>
  );
}
