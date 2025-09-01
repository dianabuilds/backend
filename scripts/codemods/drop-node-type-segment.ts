import { API, FileInfo, JSCodeshift } from 'jscodeshift';

export default function transformer(file: FileInfo, api: API) {
  const j: JSCodeshift = api.jscodeshift;
  const root = j(file.source);

  // Update route path strings
  root
    .find(j.Literal)
    .filter((p) => typeof p.value.value === 'string' && p.value.value.includes('/nodes/:type/'))
    .forEach((p) => {
      p.value.value = p.value.value.replace('/nodes/:type/', '/nodes/');
    });

  // Update template literals like `/nodes/${type}/${id}`
  root
    .find(j.TemplateLiteral)
    .forEach((p) => {
      const raw = p.value.quasis.map((q) => q.value.raw).join('${');
      if (raw.includes('/nodes/${type}/')) {
        const quasis = p.value.quasis.filter((_, i) => i !== 1);
        const expressions = p.value.expressions.filter((_, i) => i !== 0);
        p.replace(
          j.templateLiteral(quasis, expressions),
        );
      }
    });

  // Adjust useParams<{ type: string; id: string }>()
  root
    .find(j.TSTypeLiteral)
    .filter((p) =>
      p.value.members.some(
        (m) =>
          m.type === 'TSPropertySignature' &&
          m.key.type === 'Identifier' &&
          m.key.name === 'type',
      ),
    )
    .forEach((p) => {
      p.value.members = p.value.members.filter(
        (m) => !(m.type === 'TSPropertySignature' && m.key.type === 'Identifier' && m.key.name === 'type'),
      );
    });

  return root.toSource();
}
