"use client";

import { useEffect, useMemo, useState } from "react";
import { DEFAULT_MY_RADAR, type MyRadarProfile } from "@/lib/my-radar";

const UFS = ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"];

const BASE_SPECIALTIES = [
  "Anestesiologia",
  "Cardiologia",
  "Cirurgia Geral",
  "Clínica Médica",
  "Dermatologia",
  "Endocrinologia",
  "Gastroenterologia",
  "Geriatria",
  "Ginecologia e Obstetrícia",
  "Hematologia",
  "Infectologia",
  "Medicina de Emergência",
  "Medicina de Família e Comunidade",
  "Medicina do Trabalho",
  "Medicina Intensiva",
  "Medicina Legal / Perícia Médica",
  "Nefrologia",
  "Neonatologia",
  "Neurologia",
  "Oftalmologia",
  "Oncologia",
  "Ortopedia e Traumatologia",
  "Otorrinolaringologia",
  "Pediatria",
  "Pneumologia",
  "Psiquiatria",
  "Radiologia",
  "Reumatologia",
  "Urologia",
];

type Props = {
  specialties: string[];
  profile: MyRadarProfile;
  onChange: (profile: MyRadarProfile) => void;
  onlyMatches: boolean;
  onOnlyMatchesChange: (value: boolean) => void;
  contestMatches: number;
  residencyMatches: number;
};

export default function MyRadarPanel({
  specialties,
  profile,
  onChange,
  onlyMatches,
  onOnlyMatchesChange,
  contestMatches,
  residencyMatches,
}: Props) {
  const [draft, setDraft] = useState<MyRadarProfile>(profile);
  const [pin, setPin] = useState("");
  const [syncState, setSyncState] = useState<"idle" | "saving" | "ok" | "error" | "unconfigured">("idle");
  const [syncMessage, setSyncMessage] = useState("");

  useEffect(() => setDraft(profile), [profile]);

  useEffect(() => {
    fetch("/api/my-radar", { cache: "no-store" })
      .then((r) => r.json())
      .then((data) => {
        if (!data.configured) {
          setSyncState("unconfigured");
          return;
        }
        if (data.profile) {
          setSyncMessage("Perfil diário disponível para sincronização.");
        }
      })
      .catch(() => {});
  }, []);

  const sortedSpecialties = useMemo(
    () => Array.from(new Set([...BASE_SPECIALTIES, ...specialties.filter(Boolean)])).sort(),
    [specialties],
  );

  function toggleList(field: "states" | "specialties", value: string) {
    const current = draft[field];
    const next = current.includes(value)
      ? current.filter((x) => x !== value)
      : [...current, value];
    setDraft({ ...draft, [field]: next });
  }

  function save() {
    localStorage.setItem("radar:my-radar", JSON.stringify(draft));
    onChange(draft);
  }

  async function syncDaily() {
    save();
    if (!pin.trim()) {
      setSyncState("error");
      setSyncMessage("Digite o PIN administrativo.");
      return;
    }

    setSyncState("saving");
    setSyncMessage("Salvando perfil diário...");

    try {
      const response = await fetch("/api/my-radar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pin, profile: draft }),
      });
      const data = await response.json();

      if (!response.ok || !data.ok) {
        setSyncState(response.status === 503 ? "unconfigured" : "error");
        setSyncMessage(data.error || "Não foi possível sincronizar.");
        return;
      }

      setSyncState("ok");
      setSyncMessage("Alertas diários atualizados. O próximo ciclo já usará este perfil.");
      setPin("");
    } catch {
      setSyncState("error");
      setSyncMessage("Falha de conexão ao sincronizar o perfil diário.");
    }
  }

  function reset() {
    const next = { ...DEFAULT_MY_RADAR };
    localStorage.setItem("radar:my-radar", JSON.stringify(next));
    setDraft(next);
    onChange(next);
    onOnlyMatchesChange(false);
  }

  return (
    <aside className="myRadarPanel" id="meu-radar">
      <div className="myRadarBlock myRadarIntro">
        <div className="eyebrow cyan">MEU RADAR</div>
        <h3>Seu radar personalizado</h3>
        <p>Estados, especialidades e alertas salvos em um só lugar.</p>
      </div>
        <div className="myRadarBlock">
          <h3>O que acompanhar</h3>
          <div className="checkGrid compact">
            <label><input type="checkbox" checked={draft.domains.includes("contest")} onChange={() => setDraft({ ...draft, domains: draft.domains.includes("contest") ? draft.domains.filter((x) => x !== "contest") : [...draft.domains, "contest"] })}/> Concursos</label>
            <label><input type="checkbox" checked={draft.domains.includes("residency")} onChange={() => setDraft({ ...draft, domains: draft.domains.includes("residency") ? draft.domains.filter((x) => x !== "residency") : [...draft.domains, "residency"] })}/> Residências</label>
            <label><input type="checkbox" checked={draft.only_open} onChange={(e) => setDraft({ ...draft, only_open: e.target.checked })}/> Somente inscrições abertas</label>
            <label><input type="checkbox" checked={draft.official_only} onChange={(e) => setDraft({ ...draft, official_only: e.target.checked })}/> Somente com link oficial validado</label>
          </div>
        </div>

        <div className="myRadarBlock">
          <h3>Estados</h3>
          <p className="helperText">Nenhum marcado = Brasil inteiro.</p>
          <div className="chipGrid">
            {UFS.map((uf) => (
              <button key={uf} type="button" className={draft.states.includes(uf) ? "prefChip active" : "prefChip"} onClick={() => toggleList("states", uf)}>{uf}</button>
            ))}
          </div>
        </div>

        <div className="myRadarBlock">
          <h3>Especialidades</h3>
          <p className="helperText">Nenhuma marcada = todas.</p>
          <div className="chipGrid specialtiesGrid">
            {sortedSpecialties.map((sp) => (
              <button key={sp} type="button" className={draft.specialties.includes(sp) ? "prefChip active" : "prefChip"} onClick={() => toggleList("specialties", sp)}>{sp}</button>
            ))}
          </div>
        </div>

        <div className="myRadarBlock">
          <h3>Quando avisar</h3>
          <div className="checkGrid compact">
            <label><input type="checkbox" checked={draft.notify_new} onChange={(e) => setDraft({ ...draft, notify_new: e.target.checked })}/> Nova oportunidade</label>
            <label><input type="checkbox" checked={draft.notify_updates} onChange={(e) => setDraft({ ...draft, notify_updates: e.target.checked })}/> Atualização de prazo/dados</label>
            <label><input type="checkbox" checked={draft.notify_revisions} onChange={(e) => setDraft({ ...draft, notify_revisions: e.target.checked })}/> Retificação</label>
            <label className="digestSelect">Frequência
              <select value={draft.digest} onChange={(e) => setDraft({ ...draft, digest: e.target.value as "immediate" | "daily" })}>
                <option value="immediate">Avisar nas verificações do dia</option>
                <option value="daily">Resumo diário</option>
              </select>
            </label>
          </div>
        </div>

        <div className="myRadarBlock twoCols">
          <label>
            <span>Salário mínimo — concursos</span>
            <input type="number" min="0" step="500" value={draft.contest_min_salary} onChange={(e) => setDraft({ ...draft, contest_min_salary: Number(e.target.value) || 0 })}/>
          </label>
          <label>
            <span>Bolsa mínima — residência</span>
            <input type="number" min="0" step="500" value={draft.residency_min_stipend} onChange={(e) => setDraft({ ...draft, residency_min_stipend: Number(e.target.value) || 0 })}/>
          </label>
        </div>

        <div className="myRadarActions">
          <button className="button primary" type="button" onClick={save}>Salvar neste dispositivo</button>
          <button className="button secondary" type="button" onClick={reset}>Restaurar padrão</button>
          <label className="matchToggle"><input type="checkbox" checked={onlyMatches} onChange={(e) => onOnlyMatchesChange(e.target.checked)}/> Mostrar somente compatíveis</label>
        </div>

        <div className="dailySync">
          <div>
            <h3>Alertas diários</h3>
            <p>Para o robô usar este mesmo perfil mesmo com o navegador fechado, sincronize o perfil operacional.</p>
          </div>
          <div className="dailySyncControls">
            <input type="password" inputMode="numeric" value={pin} onChange={(e) => setPin(e.target.value)} placeholder="PIN administrativo" autoComplete="off"/>
            <button className="button primary" type="button" onClick={syncDaily} disabled={syncState === "saving"}>
              {syncState === "saving" ? "Sincronizando..." : "Ativar / atualizar alertas diários"}
            </button>
          </div>
          <small className={`syncStatus ${syncState}`}>
            {syncState === "unconfigured"
              ? "A ativação inicial do envio diário ainda precisa ser configurada uma única vez."
              : syncMessage || "O e-mail de destino fica protegido e não aparece nesta página."}
          </small>
        </div>

        <div className="matchSummary">
          <div><strong>{contestMatches}</strong><span>concursos compatíveis agora</span></div>
          <div><strong>{residencyMatches}</strong><span>residências compatíveis agora</span></div>
        </div>
    </aside>
  );
}
