import { categoryLabels, propertyLabels, statusLabels } from "@/lib/format";

export function Filters({ values }: { values: Record<string, string | string[] | undefined> }) {
  const selected = (key: string) => Array.isArray(values[key]) ? values[key][0] : values[key];
  return (
    <form className="filters" action="/dotacje" method="get">
      <label>Lokalizacja
        <select name="location" defaultValue={selected("location") ?? ""}>
          <option value="">Całe Mazowsze</option>
          <option value="mazowieckie">Mazowieckie</option>
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
      <button type="submit">Filtruj dotacje</button>
    </form>
  );
}
