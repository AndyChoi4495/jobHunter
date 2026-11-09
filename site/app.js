// jobs.json을 불러와 필터·검색 가능한 공고 목록을 그리는 스크립트
// Script that loads jobs.json and renders a filterable, searchable posting list
(function () {
  "use strict";
  var NEW_DAYS = 7;
  var jobs = [];
  var $ = function (id) { return document.getElementById(id); };

  // City is the part of the free-text location before the first comma.
  function cityOf(job) {
    return (job.location || "").split(",")[0].trim();
  }

  function isNew(job) {
    if (!job.posted) return false;
    var age = (Date.now() - new Date(job.posted + "T00:00:00").getTime()) / 86400000;
    return age <= NEW_DAYS;
  }

  function safeUrl(u) {
    return /^https?:\/\//i.test(u || "") ? u : null;
  }

  function fillSelect(id, values) {
    var sel = $(id);
    Array.from(new Set(values)).filter(Boolean).sort().forEach(function (v) {
      var o = document.createElement("option");
      o.value = v;
      o.textContent = v;
      sel.appendChild(o);
    });
  }

  function tag(text, cls) {
    var s = document.createElement("span");
    s.className = "tag" + (cls ? " " + cls : "");
    s.textContent = text;
    return s;
  }

  function row(job) {
    var li = document.createElement("li");
    var info = document.createElement("div");
    info.className = "info";

    var title = document.createElement("div");
    title.className = "title";
    title.textContent = job.title + " — " + job.company;
    info.appendChild(title);

    var sub = document.createElement("div");
    sub.className = "sub";
    if (isNew(job)) sub.appendChild(tag("NEW", "new"));
    sub.appendChild(tag(job.track));
    sub.appendChild(tag(job.source));
    var parts = [job.location, job.remote ? "Remote" : "", job.posted].filter(Boolean);
    sub.appendChild(document.createTextNode(parts.join(" · ")));
    info.appendChild(sub);
    li.appendChild(info);

    var href = safeUrl(job.url);
    if (href) {
      var a = document.createElement("a");
      a.className = "apply";
      a.href = href;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.textContent = "Apply";
      li.appendChild(a);
    }
    return li;
  }

  function render() {
    var q = $("q").value.trim().toLowerCase();
    var track = $("track").value, city = $("city").value, source = $("source").value;
    var shown = jobs.filter(function (j) {
      if (track && j.track !== track) return false;
      if (source && j.source !== source) return false;
      if (city && cityOf(j) !== city) return false;
      if (q && (j.company + " " + j.title + " " + j.location).toLowerCase().indexOf(q) < 0) return false;
      return true;
    });
    var list = $("list");
    list.textContent = "";
    shown.forEach(function (j) { list.appendChild(row(j)); });
    $("count").textContent = shown.length + " of " + jobs.length + " postings";
  }

  fetch("jobs.json")
    .then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    })
    .then(function (data) {
      jobs = data.jobs || [];
      $("meta").textContent = "Updated " + (data.generated_at || "unknown");
      fillSelect("track", jobs.map(function (j) { return j.track; }));
      fillSelect("city", jobs.map(cityOf));
      fillSelect("source", jobs.map(function (j) { return j.source; }));
      ["q", "track", "city", "source"].forEach(function (id) {
        $(id).addEventListener("input", render);
      });
      render();
    })
    .catch(function (e) {
      $("meta").textContent = "Could not load jobs.json (" + e.message + ").";
    });
})();
