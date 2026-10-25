import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

/**
 * Safe Markdown renderer for research reports.
 * Renders Markdown content as formatted UI with support for:
 * - Headings, paragraphs, emphasis
 * - Ordered and unordered lists
 * - Tables with proper formatting
 * - Links (opened in new tab with security attributes)
 */
function MarkdownRenderer({ content, className = '' }) {
  if (!content) {
    return null;
  }

  // Handle non-string content gracefully
  if (typeof content !== 'string') {
    return <span className="text-muted">{String(content)}</span>;
  }

  return (
    <div className={`markdown-content ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Headings with proper hierarchy
          h1: ({ children }) => (
            <h1 style={{ 
              fontSize: 'var(--font-size-xl)', 
              fontWeight: 600, 
              marginBottom: 'var(--space-4)', 
              marginTop: 'var(--space-6)',
              color: 'var(--color-text-primary)'
            }}>
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 style={{ 
              fontSize: 'var(--font-size-lg)', 
              fontWeight: 600, 
              marginBottom: 'var(--space-3)', 
              marginTop: 'var(--space-5)',
              color: 'var(--color-text-primary)'
            }}>
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 style={{ 
              fontSize: 'var(--font-size-base)', 
              fontWeight: 600, 
              marginBottom: 'var(--space-2)', 
              marginTop: 'var(--space-4)',
              color: 'var(--color-text-primary)'
            }}>
              {children}
            </h3>
          ),
          h4: ({ children }) => (
            <h4 style={{ 
              fontSize: 'var(--font-size-sm)', 
              fontWeight: 600, 
              marginBottom: 'var(--space-2)', 
              marginTop: 'var(--space-3)',
              color: 'var(--color-text-primary)'
            }}>
              {children}
            </h4>
          ),
          
          // Paragraphs with proper spacing
          p: ({ children }) => (
            <p style={{ 
              marginBottom: 'var(--space-3)', 
              lineHeight: 1.7,
              fontSize: 'var(--font-size-sm)',
              color: 'var(--color-text-secondary)'
            }}>
              {children}
            </p>
          ),
          
          // Lists
          ul: ({ children }) => (
            <ul style={{ 
              marginLeft: 'var(--space-6)', 
              marginBottom: 'var(--space-3)',
              fontSize: 'var(--font-size-sm)'
            }}>
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol style={{ 
              marginLeft: 'var(--space-6)', 
              marginBottom: 'var(--space-3)',
              fontSize: 'var(--font-size-sm)'
            }}>
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li style={{ 
              marginBottom: 'var(--space-1)',
              lineHeight: 1.6,
              color: 'var(--color-text-secondary)'
            }}>
              {children}
            </li>
          ),
          
          // Emphasis
          strong: ({ children }) => (
            <strong style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>
              {children}
            </strong>
          ),
          em: ({ children }) => (
            <em style={{ fontStyle: 'italic' }}>
              {children}
            </em>
          ),
          
          // Links - open in new tab with security attributes
          a: ({ href, children }) => (
            <a 
              href={href} 
              target="_blank" 
              rel="noopener noreferrer"
              style={{ 
                color: 'var(--color-accent)', 
                textDecoration: 'none',
                borderBottom: '1px solid var(--color-accent)'
              }}
            >
              {children}
            </a>
          ),
          
          // Tables with proper formatting
          table: ({ children }) => (
            <div style={{ overflowX: 'auto', marginBottom: 'var(--space-4)', marginTop: 'var(--space-3)' }}>
              <table style={{ 
                width: '100%', 
                borderCollapse: 'collapse',
                fontSize: 'var(--font-size-sm)'
              }}>
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
              {children}
            </thead>
          ),
          tbody: ({ children }) => <tbody>{children}</tbody>,
          tr: ({ children }) => (
            <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
              {children}
            </tr>
          ),
          th: ({ children }) => (
            <th style={{ 
              padding: 'var(--space-3)', 
              textAlign: 'left', 
              fontWeight: 600,
              borderBottom: '2px solid var(--color-border-strong)',
              fontSize: 'var(--font-size-xs)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              color: 'var(--color-text-muted)'
            }}>
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td style={{ 
              padding: 'var(--space-2) var(--space-3)',
              textAlign: 'left',
              color: 'var(--color-text-secondary)'
            }}>
              {children}
            </td>
          ),
          
          // Code blocks and inline code
          code: ({ inline, className, children }) => {
            if (inline) {
              return (
                <code style={{ 
                  backgroundColor: 'var(--color-surface-tertiary)', 
                  padding: '2px 6px', 
                  borderRadius: 'var(--radius-sm)',
                  fontSize: 'var(--font-size-xs)',
                  fontFamily: 'monospace',
                  color: 'var(--color-text-primary)'
                }}>
                  {children}
                </code>
              );
            }
            return (
              <pre style={{ 
                backgroundColor: 'var(--color-surface-secondary)', 
                padding: 'var(--space-3)', 
                borderRadius: 'var(--radius-md)',
                overflowX: 'auto',
                marginBottom: 'var(--space-3)',
                border: '1px solid var(--color-border)'
              }}>
                <code style={{ 
                  fontSize: 'var(--font-size-xs)', 
                  fontFamily: 'monospace',
                  color: 'var(--color-text-primary)'
                }}>
                  {children}
                </code>
              </pre>
            );
          },
          
          // Blockquotes
          blockquote: ({ children }) => (
            <blockquote style={{ 
              borderLeft: '4px solid var(--color-border-strong)', 
              paddingLeft: 'var(--space-4)', 
              marginLeft: 0,
              marginBottom: 'var(--space-3)',
              color: 'var(--color-text-muted)',
              fontStyle: 'italic',
              fontSize: 'var(--font-size-sm)'
            }}>
              {children}
            </blockquote>
          ),
          
          // Horizontal rules
          hr: () => (
            <hr style={{ 
              border: 'none', 
              borderTop: '1px solid var(--color-border)', 
              margin: 'var(--space-5) 0' 
            }} />
          )
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

export default MarkdownRenderer;
