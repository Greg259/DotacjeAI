import { beneficiaryLabels, categoryLabels, propertyLabels, statusLabels } from "@/lib/format";

export function Filters({ values }: { values: Record<string, string | string[] | undefined> }) {
  const selected = (key: string) => Array.isArray(values[key]) ? values[key][0] : values[key];
  return (
    <details className="filters-panel" open>
      <summary>Filtry dotacji</summary>
      <form className="filters" action="/dotacje" method="get">
      <label>Lokalizacja
        <select name="location" defaultValue={selected("location") ?? ""}>
          <option value="">Wszystkie lokalizacje</option>
          <option value="mazowieckie">Mazowieckie</option>
          <option value="pruszkowski">Powiat pruszkowski</option>
          <option value="nadarzyn">Nadarzyn</option>
        </select>
      </label>
      <label>Status
        <select name="status" defaultValue={selected("status") ?? ""}>
          <option value="">Wszystkie</option>
          {Object.entries(statusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select>
      </label>
      <label>Cel inwestycji
        <select name="category" defaultValue={selected("category") ?? ""}>
          <option value="">Wszystkie cele</option>
          {Object.entries(categoryLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select>
      </label>
      <label>Typ nieruchomości
        <select name="property_type" defaultValue={selected("property_type") ?? ""}>
          <option value="">Wszystkie</option>
          {Object.entries(propertyLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select>
      </label>
      <label>Beneficjent
        <select name="beneficiary_type" defaultValue={selected("beneficiary_type") ?? ""}>
          <option value="">Wszyscy</option>
          {Object.entries(beneficiaryLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select>
      </label>
      <label>Wielkość firmy
        <select name="business_size" defaultValue={selected("business_size") ?? ""}>
          <option value="">Dowolna</option>
          <option value="micro">Mikro</option>
          <option value="small">Mała</option>
          <option value="medium">Średnia</option>
          <option value="large">Duża</option>
        </select>
      </label>
      <label>Nabór kończy się od
        <input type="date" name="application_end_from" defaultValue={selected("application_end_from") ?? ""} />
      </label>
      <label>Nabór kończy się do
        <input type="date" name="application_end_to" defaultValue={selected("application_end_to") ?? ""} />
      </label>
      <label>Minimalna kwota
        <input type="number" min="0" step="100" name="min_amount" defaultValue={selected("min_amount") ?? ""} placeholder="np. 5000" />
      </label>
      <label>Maksymalna kwota
        <input type="number" min="0" step="100" name="max_amount" defaultValue={selected("max_amount") ?? ""} placeholder="np. 50000" />
      </label>
      <label>Wsparcie co najmniej
        <select name="min_support_percent" defaultValue={selected("min_support_percent") ?? ""}>
          <option value="">Dowolne</option>
          <option value="30">30%</option>
          <option value="40">40%</option>
          <option value="60">60%</option>
          <option value="70">70%</option>
          <option value="100">100%</option>
        </select>
      </label>
      <label>Sortowanie
        <select name="sort" defaultValue={selected("sort") ?? "ending_soon"}>
          <option value="ending_soon">Kończące się najpierw</option>
          <option value="newest">Ostatnio zweryfikowane</option>
          <option value="amount_desc">Najwyższa kwota</option>
          <option value="title">Nazwa A–Z</option>
        </select>
      </label>
      <label>Zweryfikowane od
        <input type="date" name="verified_since" defaultValue={selected("verified_since") ?? ""} />
      </label>
      <button type="submit">Filtruj dotacje</button>
      <a className="clear-filters" href="/dotacje">Wyczyść filtry</a>
      </form>
    </details>
  );
}
