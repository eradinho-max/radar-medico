"use client";

import { useEffect, useMemo, useState } from "react";
import type { Opportunity } from "@/lib/types";
import type { ResidencyOpportunity } from "@/lib/residency-types";

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
  mode: "live" | "demo" | "initializing";
  updatedAt: string | null;
  officialCount: number;
  auxiliaryCount: number;
};

export default function Home() {
  const [activeTab, setActiveTab] = useState<"concursos" | "residencias">("concursos");

  const [items, setItems] = useState<Opportunity[]>([]);
  const [meta, setMeta] = useState<DatasetMeta>({
    mode: "demo",
    updatedAt: null,
    officialCount: 0,
    auxiliaryCount: 0,
  });

  const [residencies, setResidencies] = useState<ResidencyOpportunity[]>([]);
  const [resMeta, setResMeta] = useState<DatasetMeta>({
    mode: "initializing",
    updatedAt: null,
    officialCount: 0,
    auxiliaryCount: 0,
  });

  const [query, setQuery] = useState("");
  const [state, setState] = useState("");
  const [specialty, setSpecialty] = useState("");
  const [salary, setSalary] = useState(0);
  const [status, setStatus] = useState("");

  const [resQuery, setResQuery] = useState("");
  const [resState, setResState] = useState("");
  const [resSpecialty, setResSpecialty] = useState("");
  const [resEntryType, setResEntryType] = useState("");
  const [resStipend, setResStipend] = useState(0);
  const [resStatus, setResStatus] = useState("");

  const [favorites, setFavorites] = useState<string[]>([]);
  const [contestSourceHealth, setContestSourceHealth] = useState<{
    total: number;
    healthy: number;
    errors: number;
    byRegion: Record<string, number>;
  }>({ total: 0, healthy: 0, errors: 0, byRegion: {} });
  const [resSourceHealth, setResSourceHealth] = useState<{
    total: number;
    healthy: number;
    errors: number;
    byRegion: Record<string, number>;
  }>({ total: 0, healthy: 0, errors: 0, byRegion: {} });

  useEffect(() => {
    Promise.all([
      fetch("/api/opportunities").then((r) => r.json()),
      fetch("/api/residencies").then((r) => r.json()),
      fetch("/api/residency-sources").then((r) => r.json()),
      fetch("/api/contest-sources").then((r) => r.json()),
    ]).then(([contestData, residencyData, sourceHealth, contestHealth]) => {
      setItems(contestData.items ?? []);
      setContestSourceHealth({
        total: contestHealth.total ?? 0,
        healthy: contestHealth.healthy ?? 0,
        errors: contestHealth.errors ?? 0,
        byRegion: contestHealth.byRegion ?? {},
      });
      setMeta({
        mode: contestData.mode ?? "demo",
        updatedAt: contestData.updatedAt ?? null,
        officialCount: contestData.officialCount ?? 0,
        auxiliaryCount: contestData.auxiliaryCount ?? 0,
      });

      setResidencies(residencyData.items ?? []);
      setResSourceHealth({
        total: sourceHealth.total ?? 0,
        healthy: sourceHealth.healthy ?? 0,
        errors: sourceHealth.errors ?? 0,
        byRegion: sourceHealth.byRegion ?? {},
      });
      setResMeta({
        mode: residencyData.mode ?? "initializing",
        updatedAt: residencyData.updatedAt ?? null,
        officialCount: residencyData.officialCount ?? 0,
        auxiliaryCount: residencyData.auxiliaryCount ?? 0,
      });
    });

    try {
      setFavorites(JSON.parse(localStorage.getItem("radar:favorites") || "[]"));
    } catch {}
  }, []);

  function toggleFavorite(id: string) {
    const next = favorites.includes(id)
      ? favorites.filter((x) => x !== id)
      : [...favorites, id];
    setFavorites(next);
    localStorage.setItem("radar:favorites", JSON.stringify(next));
  }

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

  const resStates = useMemo(
    () =>
      Array.from(
        new Set(residencies.map((i) => i.state).filter((x) => x && x !== "BR")),
      ).sort(),
    [residencies],
  );

  const resSpecialties = useMemo(
    () =>
      Array.from(
        new Set(residencies.map((i) => i.specialty).filter(Boolean)),
      ).sort(),
    [residencies],
  );

  const resEntryTypes = useMemo(
    () =>
      Array.from(
        new Set(
          residencies
            .map((i) => i.entryType)
            .filter((x) => x && x !== "Não informado"),
        ),
      ).sort(),
    [residencies],
  );

  const filteredResidencies = useMemo(
    () =>
      residencies
        .filter((item) => {
          const haystack =
            `${item.title} ${item.institution} ${item.city} ${item.specialty} ${item.entryType}`.toLowerCase();
          return (
            (!resQuery || haystack.includes(resQuery.toLowerCase())) &&
            (!resState || item.state === resState) &&
            (!resSpecialty || item.specialty === resSpecialty) &&
            (!resEntryType || item.entryType === resEntryType) &&
            (!resStipend || (item.stipend ?? 0) >= resStipend) &&
            (!resStatus || item.status === resStatus)
          );
        })
        .sort((a, b) =>
          (a.deadline || "9999").localeCompare(b.deadline || "9999"),
        ),
    [
      residencies,
      resQuery,
      resState,
      resSpecialty,
      resEntryType,
      resStipend,
      resStatus,
    ],
  );

  const activeMeta = activeTab === "concursos" ? meta : resMeta;
  const totalActive = activeTab === "concursos" ? items.length : residencies.length;
  const updatedLabel = activeMeta.updatedAt
    ? new Date(activeMeta.updatedAt).toLocaleString("pt-BR")
    : "aguardando coleta automática";

  return (
    <main>
      <header className="topbar">
        <div className="shell nav">
          <a href="#top" className="brand">
            <span className="brandMark">⌁</span>
            <span>Radar Médico</span>
          </a>
          <nav>
            <a href="#radar">Radar</a>
            <a href="#alertas">Alertas</a>
            <a href="#fontes">Fontes</a>
          </nav>
          <a className="button primary small" href="#radar">
            Abrir radar
          </a>
        </div>
      </header>

      <section className="hero shell" id="top">
        <div className="heroCopy">
          <div className="pill">
            <span className="liveDot" />
            {activeMeta.mode === "live" ? "RADAR LIVE" : "RADAR EM INICIALIZAÇÃO"}
          </div>
          <h1>
            Sua carreira médica,
            <br />
            <span>em um só radar.</span>
          </h1>
          <p>
            Concursos, processos seletivos e residências médicas em uma única
            ferramenta gratuita, com filtros próprios, coleta automática e
            rastreabilidade da fonte.
          </p>
          <div className="heroActions">
            <a className="button primary" href="#radar">
              Explorar radar
            </a>
            <button
              className="button secondary"
              onClick={() => {
                setActiveTab("residencias");
                document.getElementById("radar")?.scrollIntoView({ behavior: "smooth" });
              }}
            >
              Ver residências
            </button>
          </div>
          <div className="trustRow">
            <span>Concursos + Residências</span>
            <span>Atualização automática 3×/dia</span>
            <span>Custo operacional R$ 0</span>
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
              <strong>{totalActive}</strong>
              <span>{activeTab === "concursos" ? "concursos" : "residências"}</span>
            </div>
            <div>
              <strong>{activeMeta.officialCount}</strong>
              <span>fontes oficiais</span>
            </div>
            <div>
              <strong>{activeMeta.auxiliaryCount}</strong>
              <span>descobertas auxiliares</span>
            </div>
          </div>
        </div>
      </section>

      <section className="shell section" id="radar">
        <div className="radarTabs" role="tablist">
          <button
            className={activeTab === "concursos" ? "radarTab active" : "radarTab"}
            onClick={() => setActiveTab("concursos")}
          >
            Concursos Médicos
            <span>{items.length}</span>
          </button>
          <button
            className={activeTab === "residencias" ? "radarTab active" : "radarTab"}
            onClick={() => setActiveTab("residencias")}
          >
            Residências Médicas
            <span>{residencies.length}</span>
          </button>
        </div>

        {activeTab === "concursos" ? (
          <>
            <div className="sectionHead">
              <div>
                <div className="eyebrow">CONCURSOS</div>
                <h2>Concursos e processos seletivos</h2>
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
                {states.map((x) => <option key={x}>{x}</option>)}
              </select>

              <select value={specialty} onChange={(e) => setSpecialty(e.target.value)}>
                <option value="">Todas especialidades</option>
                {specialties.map((x) => <option key={x}>{x}</option>)}
              </select>

              <select value={salary} onChange={(e) => setSalary(Number(e.target.value))}>
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

              <button
                className="button secondary"
                onClick={() => {
                  setQuery("");
                  setState("");
                  setSpecialty("");
                  setSalary(0);
                  setStatus("");
                }}
              >
                Limpar
              </button>
            </div>

            <div className="resultsBar">
              <span><strong>{filtered.length}</strong> oportunidades encontradas</span>
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
                        <strong>{item.salary ? brl.format(item.salary) : "Não informada"}</strong>
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
                        ? item.officialUrl
                          ? " — destino oficial específico validado."
                          : " — edital oficial direto ainda não validado; o botão abre exatamente o anúncio deste concurso no PCI."
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
                          {item.officialUrl
                            ? "Abrir processo oficial validado"
                            : "Abrir anúncio específico no PCI"}
                        </a>
                      ) : (
                        <span className="button secondary">Sem link externo</span>
                      )}
                      <button className="button save" onClick={() => toggleFavorite(item.id)}>
                        {favorites.includes(item.id) ? "★ Salvo" : "☆ Salvar"}
                      </button>
                    </div>
                  </article>
                );
              })}
              {!filtered.length && (
                <div className="empty">Nenhuma oportunidade encontrada com esses filtros.</div>
              )}
            </div>
          </>
        ) : (
          <>
            <div className="sectionHead">
              <div>
                <div className="eyebrow cyan">RESIDÊNCIAS</div>
                <h2>Residências Médicas</h2>
                <p>
                  Editais públicos de seleção com filtros próprios. Última atualização:
                  {" "}{updatedLabel}.
                </p>
              </div>
              <span className="residencyBadge">
                {resMeta.mode === "live" ? "RADAR DE RESIDÊNCIAS" : "AGUARDANDO PRIMEIRA COLETA"}
              </span>
            </div>

            <div className="filters residencyFilters">
              <label className="searchBox">
                <span>⌕</span>
                <input
                  value={resQuery}
                  onChange={(e) => setResQuery(e.target.value)}
                  placeholder="Buscar instituição, programa ou cidade..."
                />
              </label>

              <select value={resState} onChange={(e) => setResState(e.target.value)}>
                <option value="">Todos os estados</option>
                {resStates.map((x) => <option key={x}>{x}</option>)}
              </select>

              <select value={resSpecialty} onChange={(e) => setResSpecialty(e.target.value)}>
                <option value="">Todas especialidades</option>
                {resSpecialties.map((x) => <option key={x}>{x}</option>)}
              </select>

              <select value={resEntryType} onChange={(e) => setResEntryType(e.target.value)}>
                <option value="">Qualquer tipo de entrada</option>
                {resEntryTypes.map((x) => <option key={x}>{x}</option>)}
              </select>

              <select value={resStipend} onChange={(e) => setResStipend(Number(e.target.value))}>
                <option value="0">Qualquer bolsa</option>
                <option value="3000">Bolsa ≥ R$ 3 mil</option>
                <option value="4000">Bolsa ≥ R$ 4 mil</option>
                <option value="5000">Bolsa ≥ R$ 5 mil</option>
              </select>

              <select value={resStatus} onChange={(e) => setResStatus(e.target.value)}>
                <option value="">Todos os status</option>
                <option value="open">Inscrições abertas</option>
                <option value="upcoming">Em breve</option>
              </select>

              <button
                className="button secondary"
                onClick={() => {
                  setResQuery("");
                  setResState("");
                  setResSpecialty("");
                  setResEntryType("");
                  setResStipend(0);
                  setResStatus("");
                }}
              >
                Limpar
              </button>
            </div>

            <div className="resultsBar">
              <span><strong>{filteredResidencies.length}</strong> residências encontradas</span>
              <span>Ordenação: prazo mais próximo</span>
            </div>

            <div className="cards">
              {filteredResidencies.map((item) => {
                const sourceLink = item.editalPdf || item.officialUrl || item.sourceUrl;
                return (
                  <article className="jobCard residencyCard" key={item.id}>
                    <div className="cardTop">
                      <span className="tag residencyTag">{item.entryType}</span>
                      <span className={`status ${item.status}`}>
                        {item.status === "open" ? "Inscrições abertas" : "Em breve"}
                      </span>
                    </div>

                    <h3>{item.title}</h3>
                    <p className="org">{item.institution || "Instituição não informada"}</p>
                    <p className="place">
                      {item.city || "Local não informado"} · {item.state}
                    </p>

                    <div className="facts">
                      <div>
                        <span>Bolsa</span>
                        <strong>{item.stipend ? brl.format(item.stipend) : "Não informada"}</strong>
                      </div>
                      <div>
                        <span>Vagas</span>
                        <strong>{item.vacancies || "—"}</strong>
                      </div>
                      <div>
                        <span>Prazo</span>
                        <strong>{formatDate(item.deadline)}</strong>
                      </div>
                      <div>
                        <span>Prova</span>
                        <strong>{item.examDate || "—"}</strong>
                      </div>
                    </div>

                    <div className="residencyMeta">
                      <span>{item.specialty}</span>
                      {item.board && <span>Banca: {item.board}</span>}
                      {item.fee && <span>Taxa: {brl.format(item.fee)}</span>}
                    </div>

                    <div className="sourceLine">
                      <span>{item.sourceType === "official" ? "Fonte oficial" : "Descoberta auxiliar"}:</span>
                      {" "}{item.sourceName}
                      {item.sourceType === "aggregator"
                        ? " — valide no edital oficial antes da inscrição."
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
                          {item.editalPdf
                            ? "Abrir edital"
                            : item.officialUrl
                              ? "Abrir fonte oficial"
                              : "Abrir descoberta"}
                        </a>
                      ) : (
                        <span className="button secondary">Sem link externo</span>
                      )}
                      <button
                        className="button save"
                        onClick={() => toggleFavorite(`res-${item.id}`)}
                      >
                        {favorites.includes(`res-${item.id}`) ? "★ Salvo" : "☆ Salvar"}
                      </button>
                    </div>
                  </article>
                );
              })}

              {!filteredResidencies.length && (
                <div className="empty">
                  {resMeta.mode === "initializing"
                    ? "A primeira coleta de residências ainda não foi publicada."
                    : "Nenhuma residência encontrada com esses filtros."}
                </div>
              )}
            </div>
          </>
        )}
      </section>

      <section className="shell alertSection" id="alertas">
        <div>
          <div className="eyebrow cyan">ALERTAS</div>
          <h2>Um motor para dois radares.</h2>
          <p>
            A mesma execução compara novidades e alterações de concursos e
            residências. O envio continua opcional por Gmail SMTP, sem plataforma paga.
          </p>
          <div className="featureList">
            <span>✓ Novos concursos</span>
            <span>✓ Novas residências</span>
            <span>✓ Alterações de prazo e edital</span>
          </div>
        </div>

        <div className="alertPanel">
          <label>Infraestrutura</label>
          <small>
            GitHub Actions + GitHub Release Assets + Vercel Hobby. Nenhum banco,
            API ou serviço de e-mail pago é necessário para o funcionamento básico.
          </small>
        </div>
      </section>

      <section className="shell section" id="fontes">
        <div className="sectionHead">
          <div>
            <div className="eyebrow">COBERTURA</div>
            <h2>Fontes separadas por domínio.</h2>
            <p>
              Concursos e residências compartilham a infraestrutura, mas têm
              coletores e critérios próprios.
            </p>
          </div>
        </div>

        <div className="sourceGrid">
          <div>
            <strong>01</strong>
            <h3>Concursos</h3>
            <p>{contestSourceHealth.total || "—"} fontes oficiais/configuráveis; {contestSourceHealth.healthy || "—"} responderam na última coleta.</p>
          </div>
          <div>
            <strong>02</strong>
            <h3>Residências</h3>
            <p>{resSourceHealth.total || "—"} fontes institucionais no catálogo nacional; {resSourceHealth.healthy || "—"} responderam na última coleta.</p>
          </div>
          <div>
            <strong>03</strong>
            <h3>Cobertura regional</h3>
            <p>Concursos: {Object.entries(contestSourceHealth.byRegion).map(([region,count]) => `${region}: ${count}`).join(" · ") || "aguardando"}<br/>Residências: {Object.entries(resSourceHealth.byRegion).map(([region,count]) => `${region}: ${count}`).join(" · ") || "aguardando"}</p>
          </div>
        </div>
      </section>

      <footer>
        <div className="shell">
          <span>Radar Médico · Concursos + Residências · FREE-ONLY</span>
          <span>Fontes auxiliares devem ser confirmadas no edital oficial.</span>
        </div>
      </footer>
    </main>
  );
}
