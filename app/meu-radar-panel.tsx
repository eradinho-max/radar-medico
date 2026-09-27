"use client";

import { useEffect, useMemo, useState } from "react";
import { DEFAULT_MY_RADAR, type MyRadarProfile } from "@/lib/my-radar";

const UFS = ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"];

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

  useEffect(() => setDraft(profile), [profile]);

  const sortedSpecialties = useMemo(
    () => Array.from(new Set(specialties.filter(Boolean))).sort(),
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

  function reset() {
    const next = { ...DEFAULT_MY_RADAR };
    localStorage.setItem("radar:my-radar", JSON.stringify(next));
    setDraft(next);
    onChange(next);
    onOnlyMatchesChange(false);
  }

  return (
    <section className="shell section" id="meu-radar">
      <div className="sectionHead">
        <div>
          <div className="eyebrow cyan">MEU RADAR</div>
          <h2>Suas preferências em um só lugar.</h2>
          <p>Escolha o que realmente interessa. O perfil fica salvo neste dispositivo e pode ser alterado a qualquer momento.</p>
        </div>
      </div>

      <div className="myRadarPanel">
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
          <button className="button primary" type="button" onClick={save}>Salvar Meu Radar</button>
          <button className="button secondary" type="button" onClick={reset}>Restaurar padrão</button>
          <label className="matchToggle"><input type="checkbox" checked={onlyMatches} onChange={(e) => onOnlyMatchesChange(e.target.checked)}/> Mostrar somente compatíveis</label>
        </div>

        <div className="matchSummary">
          <div><strong>{contestMatches}</strong><span>concursos compatíveis agora</span></div>
          <div><strong>{residencyMatches}</strong><span>residências compatíveis agora</span></div>
        </div>
      </div>
    </section>
  );
}
