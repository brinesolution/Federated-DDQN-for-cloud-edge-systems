\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{ieeeaccess}[2026/05/30 Local IEEE Access compatible wrapper for drafting]
\LoadClass[10pt,twocolumn]{article}
\RequirePackage[a4paper,margin=0.68in,top=0.75in,bottom=0.78in,columnsep=0.22in]{geometry}
\RequirePackage{titlesec}
\RequirePackage{authblk}
\RequirePackage{fancyhdr}
\RequirePackage{xcolor}
\definecolor{accessblue}{RGB}{0,97,163}
\setlength{\parindent}{1em}
\setlength{\parskip}{0pt}
\linespread{0.98}
\titleformat{\section}{\large\bfseries\color{accessblue}}{\thesection}{0.7em}{\MakeUppercase}
\titleformat{\subsection}{\normalsize\bfseries}{\thesubsection}{0.6em}{}
\titleformat{\subsubsection}{\normalsize\itshape}{\thesubsubsection}{0.5em}{}
\titlespacing*{\section}{0pt}{1.15ex plus .2ex}{0.75ex}
\titlespacing*{\subsection}{0pt}{0.95ex plus .2ex}{0.45ex}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{IEEE Access Draft}
\fancyhead[R]{\thepage}
\renewcommand{\headrulewidth}{0.25pt}
\newcommand{\history}[1]{\gdef\@history{#1}}
\newcommand{\doi}[1]{\gdef\@doi{#1}}
\newcommand{\tfootnote}[1]{\gdef\@tfootnote{#1}}
\newcommand{\corresp}[1]{\gdef\@corresp{#1}}
\newcommand{\headeretal}{\textit{et al.}}
\newcommand{\authorrefmark}[1]{\textsuperscript{#1}}
\newcommand{\IEEEmembership}[1]{#1}
\newcommand{\PARstart}[2]{#1#2}
\newcommand{\appendices}{\appendix}
\def\@history{}
\def\@doi{}
\def\@tfootnote{}
\def\@corresp{}
\renewcommand{\maketitle}{%
  \twocolumn[{%
  \begin{center}
    {\small \@history\par}
    \vspace{0.4em}
    {\LARGE\bfseries\@title\par}
    \vspace{0.75em}
    {\normalsize\@author\par}
    \vspace{0.5em}
    {\small\itshape \@corresp\par}
    \vspace{0.35em}
    {\small DOI: \@doi\par}
    \vspace{0.8em}
  \end{center}
  }]%
  \thispagestyle{fancy}
  \footnotetext[0]{\@tfootnote}
}
\newenvironment{keywords}{\par\noindent\textbf{Index Terms---}\ignorespaces}{\par\vspace{0.7em}}
\renewenvironment{abstract}{\par\noindent\textbf{Abstract---}\ignorespaces}{\par\vspace{0.7em}}
