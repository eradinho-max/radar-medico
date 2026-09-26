"use client";

import { useEffect, useMemo, useState } from "react";
import type { Opportunity } from "@/lib/types";

const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
const dateFmt = new Intl.DateTimeFormat("pt-BR", { timeZone: "UTC", day: "2-digit", month: "2-digit", year: "numeric" });

function formatDate(value: string | null) {
  if (!value) return "não informado";
  return dateFmt.format(new Date(`${value}T12:00:00Z`));
}

export default function Home() {
  const [items, setItems] = useState<Opportunity[]>([]);
  const [query, setQuery] = useState("");
  const [state, setState] = useState("");
  const [specialty, setSpecialty] = useState("");
  const [salary, setSalary] = useState(0);
  const [status, setStatus] = useState("");
  const [favorites, setFavorites] = useState<string[]>([]);
  const [email, setEmail] = useState("");
  const [alertMessage, setAlertMessage] = useState("");

  useEffect(() => {
    fetch("/api/opportunities").then(r => r.json()).then(data => setItems(data.items ?? []));
    try { setFavorites(JSON.parse(localStorage.getItem("radar:favorites") || "[]")); } catch {}
  }, []);

  const states = useMemo(() => Array.from(new Set(items.map(i => i.state))).sort(), [items]);
  const specialties = useMemo(() => Array.from(new Set(items.map(i => i.specialty))).sort(), [items]);

  const filtered = useMemo(() => items.filter(item => {
    const haystack = `${item.title} ${item.organization} ${item.city} ${item.specialty}`.toLowerCase();
    return (!query || haystack.includes(query.toLowerCase())) &&
      (!state || item.state === state) &&
      (!specialty || item.specialty === specialty) &&
      (!salary || (item.salary ?? 0) >= salary) &&
      (!status || item.status === status);
  }).sort((a,b) => (a.deadline || "9999").localeCompare(b.deadline || "9999")), [items, query, state, specialty, salary, status]);

  function toggleFavorite(id: string) {
    const next = favorites.includes(id) ? favorites.filter(x => x !== id) : [...favorites, id];
    setFavorites(next);
    localStorage.setItem("radar:favorites", JSON.stringify(next));
  }

  function saveAlert() {
    if (!/^\S+@\S+\.\S+$/.test(email.trim())) {
      setAlertMessage("Informe um e-mail válido.");
      return;
    }
    const payload = { email: email.trim(), query, state, specialty, salary, status, daily: true, retifications: true };
    localStorage.setItem("radar:alert-draft", JSON.stringify(payload));
    setAlertMessage("Preferências salvas neste dispositivo. O disparo por e-mail será ativado no backend.");
  }

  function clearFilters() {
    setQuery(""); setState(""); setSpecialty(""); setSalary(0); setStatus("");
  }

  return (
    <main>
      <header className="topbar">
        <div className="shell nav">
          <a href="#top" className="brand"><span className="brandMark">⌁</span><span>Radar Médico</span></a>
          <nav><a href="#oportunidades">Oportunidades</a><a href="#alertas">Alertas</a><a href="#fontes">Fontes</a></nav>
          <a className="button primary small" href="#alertas">Criar alerta</a>
        </div>
      </header>

      <section className="hero shell" id="top">
        <div className="heroCopy">
          <div className="pill"><span className="liveDot"/>Monitoramento nacional</div>
          <h1>Concursos médicos,<br/><span>sem perder o prazo.</span></h1>
          <p>Um radar dedicado a médicos para localizar concursos, processos seletivos e editais em todo o Brasil — com filtros clínicos, rastreabilidade da fonte e alertas personalizados.</p>
          <div className="heroActions"><a className="button primary" href="#oportunidades">Explorar oportunidades</a><a className="button secondary" href="#alertas">Receber por e-mail</a></div>
          <div className="trustRow"><span>27 UFs</span><span>Fontes oficiais primeiro</span><span>Deduplicação planejada</span></div>
        </div>
        <div className="radarCard" aria-hidden="true">
          <div className="radar"><i className="ping one"/><i className="ping two"/><i className="ping three"/><div className="sweep"/></div>
          <div className="metrics"><div><strong>{items.length}</strong><span>itens demo</span></div><div><strong>24/7</strong><span>coleta alvo</span></div><div><strong>E-mail</strong><span>alerta gratuito</span></div></div>
        </div>
      </section>

      <section className="shell section" id="oportunidades">
        <div className="sectionHead"><div><div className="eyebrow">RADAR</div><h2>Oportunidades</h2><p>Use filtros pensados para carreira médica, não para concursos genéricos.</p></div><span className="demoBadge">DADOS DE DEMONSTRAÇÃO</span></div>
        <div className="filters">
          <label className="searchBox"><span>⌕</span><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Buscar cargo, órgão ou cidade..."/></label>
          <select value={state} onChange={e=>setState(e.target.value)}><option value="">Todos os estados</option>{states.map(x=><option key={x}>{x}</option>)}</select>
          <select value={specialty} onChange={e=>setSpecialty(e.target.value)}><option value="">Todas especialidades</option>{specialties.map(x=><option key={x}>{x}</option>)}</select>
          <select value={salary} onChange={e=>setSalary(Number(e.target.value))}><option value="0">Qualquer salário</option><option value="8000">≥ R$ 8 mil</option><option value="10000">≥ R$ 10 mil</option><option value="15000">≥ R$ 15 mil</option></select>
          <select value={status} onChange={e=>setStatus(e.target.value)}><option value="">Todos os status</option><option value="open">Inscrições abertas</option><option value="upcoming">Em breve</option></select>
          <button className="button secondary" onClick={clearFilters}>Limpar</button>
        </div>
        <div className="resultsBar"><span><strong>{filtered.length}</strong> oportunidades encontradas</span><span>Ordenação: prazo mais próximo</span></div>
        <div className="cards">
          {filtered.map(item => (
            <article className="jobCard" key={item.id}>
              <div className="cardTop"><span className="tag">{item.modality}</span><span className={`status ${item.status}`}>{item.status === "open" ? "Inscrições abertas" : "Em breve"}</span></div>
              <h3>{item.title}</h3><p className="org">{item.organization}</p><p className="place">{item.city} · {item.state}</p>
              <div className="facts"><div><span>Remuneração</span><strong>{item.salary ? brl.format(item.salary) : "Não informada"}</strong></div><div><span>Carga horária</span><strong>{item.workload || "—"}</strong></div><div><span>Vagas</span><strong>{item.vacancies || "—"}</strong></div><div><span>Prazo</span><strong>{formatDate(item.deadline)}</strong></div></div>
              <div className="specialty">{item.specialty}</div>
              <div className="sourceLine"><span>Fonte:</span> {item.sourceName}</div>
              <div className="cardActions"><button className="button secondary" onClick={()=>alert("Esta oportunidade é demonstrativa. O link oficial será habilitado quando a coleta real entrar no ar.")}>Ver detalhes</button><button className="button save" onClick={()=>toggleFavorite(item.id)}>{favorites.includes(item.id) ? "★ Salvo" : "☆ Salvar"}</button></div>
            </article>
          ))}
          {!filtered.length && <div className="empty">Nenhuma oportunidade encontrada com esses filtros.</div>}
        </div>
      </section>

      <section className="shell alertSection" id="alertas">
        <div><div className="eyebrow cyan">ALERTAS</div><h2>Seu radar pessoal no e-mail.</h2><p>Salve um filtro agora. No macrobloco de backend, novos editais e retificações serão comparados com essas preferências antes do disparo.</p><div className="featureList"><span>✓ Resumo diário</span><span>✓ Novos editais prioritários</span><span>✓ Retificações</span></div></div>
        <div className="alertPanel"><label>E-mail para receber alertas</label><div className="alertInput"><input value={email} onChange={e=>setEmail(e.target.value)} type="email" placeholder="seu@email.com"/><button className="button primary" onClick={saveAlert}>Salvar alerta</button></div><small>{alertMessage || "Nesta versão, as preferências ficam armazenadas localmente até o backend ser conectado."}</small></div>
      </section>

      <section className="shell section" id="fontes"><div className="sectionHead"><div><div className="eyebrow">COBERTURA</div><h2>Fontes com rastreabilidade.</h2><p>A arquitetura separa coleta, classificação e apresentação para cada oportunidade apontar para a origem oficial.</p></div></div><div className="sourceGrid"><div><strong>01</strong><h3>Oficiais</h3><p>DOU, governos, prefeituras, secretarias, universidades, hospitais e empresas públicas.</p></div><div><strong>02</strong><h3>Bancas</h3><p>Páginas de concursos e seleções das organizadoras, sempre vinculadas ao edital correspondente.</p></div><div><strong>03</strong><h3>Agregadores</h3><p>Somente como descoberta auxiliar. A publicação no Radar exigirá confirmação da fonte primária.</p></div></div></section>

      <footer><div className="shell"><span>Radar Médico · V0.2</span><span>Informações reais sempre devem apontar para o edital oficial.</span></div></footer>
    </main>
  );
}
