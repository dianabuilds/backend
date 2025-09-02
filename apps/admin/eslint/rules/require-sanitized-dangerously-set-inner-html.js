export default {
  meta: {
    type: 'problem',
    docs: {
      description: 'require sanitizeHtml or DOMPurify.sanitize with dangerouslySetInnerHTML',
    },
    schema: [],
    messages: {
      unsanitized: 'dangerouslySetInnerHTML must use sanitizeHtml or DOMPurify.sanitize',
    },
  },
  create(context) {
    function getCalleeName(node) {
      if (node.type === 'Identifier') {
        return node.name;
      }
      if (node.type === 'MemberExpression' && !node.computed) {
        if (node.object.type === 'Identifier' && node.property.type === 'Identifier') {
          return `${node.object.name}.${node.property.name}`;
        }
      }
      return null;
    }
    return {
      JSXAttribute(node) {
        if (node.name.name !== 'dangerouslySetInnerHTML') {
          return;
        }
        const value = node.value;
        if (!value || value.type !== 'JSXExpressionContainer') {
          context.report({ node, messageId: 'unsanitized' });
          return;
        }
        const expr = value.expression;
        if (expr.type !== 'ObjectExpression') {
          context.report({ node, messageId: 'unsanitized' });
          return;
        }
        const htmlProp = expr.properties.find(
          (p) =>
            p.type === 'Property' &&
            !p.computed &&
            ((p.key.type === 'Identifier' && p.key.name === '__html') ||
              (p.key.type === 'Literal' && p.key.value === '__html')),
        );
        if (!htmlProp) {
          context.report({ node, messageId: 'unsanitized' });
          return;
        }
        const htmlValue = htmlProp.value;
        if (htmlValue.type === 'CallExpression') {
          const calleeName = getCalleeName(htmlValue.callee);
          if (calleeName === 'sanitizeHtml' || calleeName === 'DOMPurify.sanitize') {
            return;
          }
        }
        context.report({ node, messageId: 'unsanitized' });
      },
    };
  },
};
