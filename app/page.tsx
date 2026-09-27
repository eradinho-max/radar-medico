"use client";

import { useEffect, useMemo, useState } from "react";
import type { Opportunity } from "@/lib/types";

const brl = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  maximumFractionDigits: 0,
});
const dateFmt = new Intl.DateTimeFormat("pt-BR", {
  timeZone: "UTC",
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});

function formatDate(value: string | null) {
  if (!value) return "não informado";
  return dateFmt.format(new Date(`${value}T12:00:00Z`));
}

type DatasetMeta = {
  mode: "live" | "demo";
  updatedAt: string | null;
  officialCount: number;
  auxiliaryCount: number;
};

export default function Home() {
  const [items, setItems] = useState<Opportunity[]>([]);
  const [meta, setMeta] = useState<DatasetMeta>({
    mode: "demo",
    updatedAt: null,
    officialCount: 0,
    auxiliaryCount: 0,
  });
  const [query, setQuery] = useState("");
  const [state, setState] = useState("");
  const [specialty, setSpecialty] = useState("");
  const [salary, setSalary] = useState(0);
  const [status, setStatus] = useState("");
  const [favorites, setFavorites] = useState<string[]>([]);

  useEffect(() => {
    fetch("/api/opportunities")
      .then((r) => r.json())
      .then((data) => {
        setItems(data.items ?? []);
        setMeta({
          mode: data.mode === "live" ? "live" : "demo",
          updatedAt: data.updatedAt ?? null,
          officialCount: data.officialCount ?? 0,
          auxiliaryCount: data.auxiliaryCount ?? 0,
        });
      });
    try {
      setFavorites(JSON.parse(localStorage.getItem("radar:favorites") || "[]"));
    } catch {}
  }, []);

  const states = useMemo(
    () => Array.from(new Set(items.map((i) => i.state).filter(Boolean))).sort(),
    [items],
  );
  const specialties = useMemo(
    () => Array.from(new Set(items.map((i) => i.specialty).filter(Boolean))).sort(),
    [items],
  );

  const filtered = useMemo(
    () =>
      items
        .filter((item) => {
          const haystack =
            `${item.title} ${item.organization} ${item.city} ${item.specialty}`.toLowerCase();
          return (
            (!query || haystack.includes(query.toLowerCase())) &&
            (!state || item.state === state) &&
            (!specialty || item.specialty === specialty) &&
            (!salary || (item.salary ?? 0) >= salary) &&
            (!status || item.status === status)
          );
        })
        .sort((a, b) =>
          (a.deadline || "9999").localeCompare(b.deadline || "9999"),
        ),
    [items, query, state, specialty, salary, status],
  );

  function toggleFavorite(id: string) {
    const next = favorites.includes(id)
      ? favorites.filter((x) => x !== id)
      : [...favorites, id];
    setFavorites(next);
    localStorage.setItem("radar:favorites", JSON.stringify(next));
  }

  function clearFilters() {
    setQuery("");
    setState("");
    setSpecialty("");
    setSalary(0);
    setStatus("");
  }

  const updatedLabel = meta.updatedAt
    ? new Date(meta.updatedAt).toLocaleString("pt-BR")
    : "aguardando primeira coleta automática";

  return (
    <main>
      <header className="topbar">
        <div className="shell nav">
          <a href="#top" className="brand">
            <span className="brandMark">⌁</span>
            <span>Radar Médico</span>
          </a>
          <nav>
            <a href="#oportunidades">Oportunidades</a>
            <a href="#alertas">Alertas</a>
            <a href="#fontes">Fontes</a>
          </nav>
          <a className="button primary small" href="#oportunidades">
            Abrir radar
          </a>
        </div>
      </header>

      <section className="hero shell" id="top">
        <div className="heroCopy">
          <div className="pill">
            <span className="liveDot" />
            {meta.mode === "live" ? "RADAR LIVE" : "INICIALIZANDO RADAR"}
          </div>
          <h1>
            Concursos médicos,
            <br />
            <span>sem perder o prazo.</span>
          </h1>
          <p>
            Radar gratuito de concursos, processos seletivos e editais para
            médicos, com coleta automática, filtros clínicos e rastreabilidade
            da origem.
          </p>
          <div className="heroActions">
            <a className="button primary" href="#oportunidades">
              Explorar oportunidades
            </a>
            <a className="button secondary" href="#fontes">
              Ver cobertura
            </a>
          </div>
          <div className="trustRow">
            <span>Atualização automática 3×/dia</span>
            <span>Custo operacional R$ 0</span>
            <span>Fontes oficiais primeiro</span>
          </div>
        </div>

        <div className="radarCard" aria-hidden="true">
          <div className="radar">
            <i className="ping one" />
            <i className="ping two" />
            <i className="ping three" />
            <div className="sweep" />
          </div>
          <div className="metrics">
            <div>
              <strong>{items.length}</strong>
              <span>oportunidades</span>
            </div>
            <div>
              <strong>{meta.officialCount}</strong>
              <span>fontes oficiais</span>
            </div>
            <div>
              <strong>{meta.auxiliaryCount}</strong>
              <span>descobertas auxiliares</span>
            </div>
          </div>
        </div>
      </section>

      <section className="shell section" id="oportunidades">
        <div className="sectionHead">
          <div>
            <div className="eyebrow">RADAR</div>
            <h2>Oportunidades</h2>
            <p>Última atualização: {updatedLabel}.</p>
          </div>
          <span className="demoBadge">
            {meta.mode === "live" ? "DADOS OPERACIONAIS" : "FALLBACK DEMONSTRATIVO"}
          </span>
        </div>

        <div className="filters">
          <label className="searchBox">
            <span>⌕</span>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Buscar cargo, órgão ou cidade..."
            />
          </label>

          <select value={state} onChange={(e) => setState(e.target.value)}>
            <option value="">Todos os estados</option>
            {states.map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>

          <select
            value={specialty}
            onChange={(e) => setSpecialty(e.target.value)}
          >
            <option value="">Todas especialidades</option>
            {specialties.map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>

          <select
            value={salary}
            onChange={(e) => setSalary(Number(e.target.value))}
          >
            <option value="0">Qualquer salário</option>
            <option value="8000">≥ R$ 8 mil</option>
            <option value="10000">≥ R$ 10 mil</option>
            <option value="15000">≥ R$ 15 mil</option>
          </select>

          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">Todos os status</option>
            <option value="open">Inscrições abertas</option>
            <option value="upcoming">Em breve</option>
          </select>

          <button className="button secondary" onClick={clearFilters}>
            Limpar
          </button>
        </div>

        <div className="resultsBar">
          <span>
            <strong>{filtered.length}</strong> oportunidades encontradas
          </span>
          <span>Ordenação: prazo mais próximo</span>
        </div>

        <div className="cards">
          {filtered.map((item) => {
            const sourceLink = item.officialUrl || item.sourceUrl || null;
            const sourceLabel =
              item.sourceType === "official"
                ? "Fonte oficial"
                : item.sourceType === "aggregator"
                  ? "Descoberta auxiliar"
                  : "Demonstração";

            return (
              <article className="jobCard" key={item.id}>
                <div className="cardTop">
                  <span className="tag">{item.modality}</span>
                  <span className={`status ${item.status}`}>
                    {item.status === "open" ? "Inscrições abertas" : "Em breve"}
                  </span>
                </div>

                <h3>{item.title}</h3>
                <p className="org">{item.organization}</p>
                <p className="place">
                  {item.city || "Local não informado"} · {item.state}
                </p>

                <div className="facts">
                  <div>
                    <span>Remuneração</span>
                    <strong>
                      {item.salary
                        ? brl.format(item.salary)
                        : "Não informada"}
                    </strong>
                  </div>
                  <div>
                    <span>Carga horária</span>
                    <strong>{item.workload || "—"}</strong>
                  </div>
                  <div>
                    <span>Vagas</span>
                    <strong>{item.vacancies || "—"}</strong>
                  </div>
                  <div>
                    <span>Prazo</span>
                    <strong>{formatDate(item.deadline)}</strong>
                  </div>
                </div>

                <div className="specialty">{item.specialty}</div>
                <div className="sourceLine">
                  <span>{sourceLabel}:</span> {item.sourceName}
                  {item.sourceType === "aggregator"
                    ? " — confirme sempre no edital oficial."
                    : ""}
                </div>

                <div className="cardActions">
                  {sourceLink ? (
                    <a
                      className="button secondary"
                      href={sourceLink}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {item.sourceType === "official"
                        ? "Abrir fonte oficial"
                        : "Abrir descoberta"}
                    </a>
                  ) : (
                    <span className="button secondary">Sem link externo</span>
                  )}
                  <button
                    className="button save"
                    onClick={() => toggleFavorite(item.id)}
                  >
                    {favorites.includes(item.id) ? "★ Salvo" : "☆ Salvar"}
                  </button>
                </div>
              </article>
            );
          })}

          {!filtered.length && (
            <div className="empty">
              Nenhuma oportunidade encontrada com esses filtros.
            </div>
          )}
        </div>
      </section>

      <section className="shell alertSection" id="alertas">
        <div>
          <div className="eyebrow cyan">ALERTAS</div>
          <h2>Alertas automáticos sem plataforma paga.</h2>
          <p>
            O motor já compara a coleta nova com o estado anterior e prepara
            apenas novidades e alterações. O envio usa Gmail SMTP quando os
            três segredos do repositório estiverem configurados.
          </p>
          <div className="featureList">
            <span>✓ Novas oportunidades</span>
            <span>✓ Alterações detectadas</span>
            <span>✓ Sem cobrança por e-mail</span>
          </div>
        </div>

        <div className="alertPanel">
          <label>Estado do módulo de alertas</label>
          <small>
            Coleta e comparação já são automáticas. Para receber os e-mails,
            basta configurar uma única vez RADAR_EMAIL_TO, GMAIL_SMTP_USER e
            GMAIL_APP_PASSWORD nos Secrets do GitHub.
          </small>
        </div>
      </section>

      <section className="shell section" id="fontes">
        <div className="sectionHead">
          <div>
            <div className="eyebrow">COBERTURA</div>
            <h2>Fontes com rastreabilidade.</h2>
            <p>
              A infraestrutura está congelada; daqui para frente a evolução é
              aumentar cobertura e enriquecer dados, sem trocar a arquitetura.
            </p>
          </div>
        </div>

        <div className="sourceGrid">
          <div>
            <strong>01</strong>
            <h3>Oficiais</h3>
            <p>
              Ministério da Saúde e HU Brasil/EBSERH já entram no motor oficial.
            </p>
          </div>
          <div>
            <strong>02</strong>
            <h3>Descoberta</h3>
            <p>
              PCI é usado como radar auxiliar por especialidade, nunca como
              substituto do edital oficial.
            </p>
          </div>
          <div>
            <strong>03</strong>
            <h3>Próxima expansão</h3>
            <p>
              DOU, estados, prefeituras, universidades, hospitais e bancas em
              ondas de cobertura.
            </p>
          </div>
        </div>
      </section>

      <footer>
        <div className="shell">
          <span>Radar Médico · FREE-ONLY</span>
          <span>Informações auxiliares devem ser confirmadas no edital oficial.</span>
        </div>
      </footer>
    </main>
  );
}
