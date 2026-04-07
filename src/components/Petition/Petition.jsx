import { useState } from 'react'
import './Petition.css'

const STORAGE_KEY = 'tarot-ciberquilombola-petition'

function loadSignatures() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || []
  } catch {
    return []
  }
}

export default function Petition() {
  const [tab, setTab] = useState('petition') // 'petition' | 'manifesto'
  const [name, setName] = useState('')
  const [city, setCity] = useState('')
  const [signed, setSigned] = useState(false)
  const [signatures, setSignatures] = useState(loadSignatures)

  function handleSign(e) {
    e.preventDefault()
    if (!name.trim()) return
    const entry = {
      name: name.trim(),
      city: city.trim() || null,
      date: new Date().toISOString().slice(0, 10),
    }
    const updated = [...signatures, entry]
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
    setSignatures(updated)
    setSigned(true)
    setName('')
    setCity('')
  }

  return (
    <div className="petition">
      <div className="petition__tabs">
        <button
          className={`petition__tab ${tab === 'petition' ? 'petition__tab--active' : ''}`}
          onClick={() => setTab('petition')}
        >
          Abaixo-assinado
        </button>
        <button
          className={`petition__tab ${tab === 'manifesto' ? 'petition__tab--active' : ''}`}
          onClick={() => setTab('manifesto')}
        >
          Manifesto
        </button>
      </div>

      {tab === 'petition' ? (
        <div className="petition__content">
          <h2 className="petition__title">
            Pela publica&ccedil;&atilde;o de <em>Platform for Change</em> em portugu&ecirc;s a pre&ccedil;os acess&iacute;veis
          </h2>

          <div className="petition__comparison">
            <div className="petition__price petition__price--beer">
              <span className="petition__price-label">Platform for Change</span>
              <span className="petition__price-author">Stafford Beer, 1975</span>
              <span className="petition__price-value petition__price-value--high">US$ 65&ndash;78</span>
              <span className="petition__price-note">Novo, em ingl&ecirc;s. Sem tradu&ccedil;&atilde;o para o portugu&ecirc;s.</span>
              <span className="petition__price-note">Usado a partir de US$ 47</span>
            </div>
            <div className="petition__price petition__price--bispo">
              <span className="petition__price-label">A Terra D&aacute;, A Terra Quer</span>
              <span className="petition__price-author">Ant&ocirc;nio Bispo dos Santos, 2023</span>
              <span className="petition__price-value petition__price-value--low">R$ 53</span>
              <span className="petition__price-note">Novo, em portugu&ecirc;s. Editora Ubu.</span>
              <span className="petition__price-note">&asymp; US$ 10</span>
            </div>
          </div>

          <div className="petition__text">
            <p>
              H&aacute; meio s&eacute;culo, Stafford Beer publicou <em>Platform for Change</em> &mdash; treze argumentos
              para a transforma&ccedil;&atilde;o de como organizamos a vida coletiva. O livro nunca foi traduzido
              para o portugu&ecirc;s. Custa entre US$ 65 e US$ 78 novo (cerca de R$ 350&ndash;420), valor
              inacess&iacute;vel para a maioria dos leitores brasileiros, latino-americanos e africanos de l&iacute;ngua portuguesa.
            </p>
            <p>
              Enquanto isso, <em>A Terra D&aacute;, A Terra Quer</em> de Ant&ocirc;nio Bispo dos Santos &mdash;
              obra fundamental do pensamento quilombola &mdash; custa R$ 53 na Editora Ubu. Um livro
              que transforma vis&otilde;es de mundo est&aacute; acess&iacute;vel. O outro, n&atilde;o.
            </p>
            <p>
              Beer sonhou com sistemas que servissem ao povo, n&atilde;o ao mercado. Bispo nos
              ensinou que o saber que n&atilde;o circula apodrece. <strong>Um livro trancado atr&aacute;s de um
              pre&ccedil;o proibitivo contradiz o pr&oacute;prio conte&uacute;do que carrega.</strong>
            </p>
            <p>
              Pedimos aos detentores dos direitos autorais de Stafford Beer e &agrave; editora
              Wiley que viabilizem uma edi&ccedil;&atilde;o em portugu&ecirc;s de <em>Platform for Change</em>
              a pre&ccedil;os compat&iacute;veis com a realidade do Sul Global &mdash; idealmente na faixa
              de R$ 50&ndash;80, como as obras de pensamento cr&iacute;tico j&aacute; publicadas no Brasil.
            </p>

            <h3>Ao assinar, voc&ecirc; autoriza:</h3>
            <ul>
              <li>Que o organizador desta peti&ccedil;&atilde;o endre&ccedil;e a lista de signat&aacute;rios aos detentores dos direitos autorais de Stafford Beer e &agrave; editora Wiley &amp; Sons;</li>
              <li>Que seu nome e cidade (se informada) sejam listados publicamente como signat&aacute;rio(a);</li>
              <li>Que a peti&ccedil;&atilde;o seja enviada a editoras brasileiras e portuguesas como demonstra&ccedil;&atilde;o de demanda por uma edi&ccedil;&atilde;o acess&iacute;vel.</li>
            </ul>
          </div>

          {signed ? (
            <div className="petition__thanks">
              <p>Assinatura registrada. Obrigado por apoiar o acesso ao conhecimento sist&ecirc;mico.</p>
            </div>
          ) : (
            <form className="petition__form" onSubmit={handleSign}>
              <div className="petition__field">
                <label htmlFor="pet-name">Nome completo *</label>
                <input
                  id="pet-name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  placeholder="Seu nome"
                />
              </div>
              <div className="petition__field">
                <label htmlFor="pet-city">Cidade / Pa&iacute;s</label>
                <input
                  id="pet-city"
                  type="text"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  placeholder="Ex: S&atilde;o Paulo, Brasil"
                />
              </div>
              <button type="submit" className="petition__submit">
                Assinar peti&ccedil;&atilde;o
              </button>
            </form>
          )}

          {signatures.length > 0 && (
            <div className="petition__signatures">
              <h3>{signatures.length} signat&aacute;rio{signatures.length > 1 ? 's' : ''}</h3>
              <ul>
                {signatures.map((s, i) => (
                  <li key={i}>
                    <strong>{s.name}</strong>
                    {s.city && <span> &mdash; {s.city}</span>}
                    <span className="petition__sig-date"> ({s.date})</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : (
        <div className="petition__content petition__manifesto">
          <h2 className="petition__title">
            Manifesto: Cibern&eacute;tica &amp; Quilombo
          </h2>
          <h3 className="petition__manifesto-sub">
            Por que Beer e Bispo precisam se encontrar em portugu&ecirc;s
          </h3>

          <blockquote className="petition__quote petition__quote--beer">
            <p>&ldquo;The purpose of a system is what it does.&rdquo;</p>
            <cite>&mdash; Stafford Beer, 1974</cite>
          </blockquote>

          <blockquote className="petition__quote petition__quote--bispo">
            <p>&ldquo;N&oacute;s n&atilde;o somos o que dizemos que somos. N&oacute;s somos o que fazemos.&rdquo;</p>
            <cite>&mdash; Ant&ocirc;nio Bispo dos Santos</cite>
          </blockquote>

          <div className="petition__manifesto-body">
            <p>
              Dois homens. Dois continentes. Duas tradi&ccedil;&otilde;es de pensamento que nunca se
              encontraram em vida &mdash; mas dizem a mesma coisa em linguagens diferentes.
            </p>
            <p>
              <strong>Stafford Beer</strong> (1926&ndash;2002), ciberneticista brit&acirc;nico, passou a vida
              construindo ferramentas para que organiza&ccedil;&otilde;es complexas pudessem se conhecer a
              si mesmas. Seu Modelo de Sistema Vi&aacute;vel n&atilde;o &eacute; uma teoria de controle &mdash; &eacute;
              uma teoria de <em>autonomia</em>: como cada parte de um sistema pode governar a si
              mesma sem perder coer&ecirc;ncia com o todo. Beer sonhou com um socialismo
              cibern&eacute;tico no Chile de Allende. O golpe destruiu o sonho, n&atilde;o a id&eacute;ia.
            </p>
            <p>
              <strong>Ant&ocirc;nio Bispo dos Santos</strong> (1959&ndash;2023), lavrador e pensador
              quilombola do Piau&iacute;, viveu o que Beer teorizou. Os quilombos s&atilde;o sistemas
              vi&aacute;veis &mdash; comunidades que mantiveram exist&ecirc;ncia aut&ocirc;noma sob condi&ccedil;&otilde;es
              de opress&atilde;o extrema, desenvolvendo circuitos de informa&ccedil;&atilde;o oral,
              ferramentas de trabalho coletivo, sinais alged&ocirc;nicos corporificados e
              territ&oacute;rios de identidade que resistiram a s&eacute;culos de viol&ecirc;ncia colonial.
            </p>
            <p>
              Beer chamava de <em>homeostase</em> o que Bispo chamava de <em>equil&iacute;brio da terra</em>.
              Beer falava em <em>variedade requerida</em>; Bispo dizia que <em>&ldquo;a terra n&atilde;o &eacute; uma s&oacute;&rdquo;</em>.
              Beer projetava <em>canais alged&ocirc;nicos</em> para que a dor do sistema chegasse ao
              centro de decis&atilde;o; nos quilombos, <em>o tambor j&aacute; fazia isso h&aacute; s&eacute;culos</em>.
            </p>
            <p>
              O problema &eacute; simples: <strong>Beer est&aacute; trancado em ingl&ecirc;s caro. Bispo est&aacute;
              acess&iacute;vel em portugu&ecirc;s.</strong> O di&aacute;logo que deveria acontecer &mdash; entre
              cibern&eacute;tica ocidental e epistemologia quilombola &mdash; n&atilde;o pode acontecer
              enquanto um dos interlocutores custa sete vezes mais que o outro.
            </p>
            <p>
              <em>Platform for Change</em> n&atilde;o &eacute; um livro de gest&atilde;o. &Eacute; um chamado para
              reorganizar a sociedade usando a intelig&ecirc;ncia dos sistemas vivos. Cada um
              dos treze argumentos de Beer poderia ter sido escrito por Bispo em outra
              linguagem &mdash; a linguagem da terra, do mutir&atilde;o, do terreiro.
            </p>
            <p>
              <strong>Este manifesto pede uma coisa:</strong> que o pensamento sist&ecirc;mico deixe de
              ser privil&eacute;gio de quem l&ecirc; ingl&ecirc;s e pode pagar US$ 70 por um livro. Que
              Beer e Bispo possam finalmente se encontrar na mesma l&iacute;ngua, na mesma
              estante, ao alcance da mesma m&atilde;o.
            </p>
            <p className="petition__manifesto-close">
              Porque o prop&oacute;sito de um livro &eacute; o que ele faz.<br />
              E um livro que n&atilde;o pode ser lido n&atilde;o faz nada.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
