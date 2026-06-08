// Quando o documento estiver carregado
document.addEventListener("DOMContentLoaded", function() {
    // Quando o botão de pesquisa for clicado
    document.getElementById("botaoPesquisar").addEventListener("click", function() {
        // Pega o termo de pesquisa e o tipo selecionado
        const termo = document.getElementById("pesquisa").value;
        const tipo = document.querySelector('input[name="tipo"]:checked').value;

        // Se o botão diz "Voltar", recarrega a página
        if (this.textContent === "Voltar") {
            location.reload();
            return;
        }

        // Se o termo de pesquisa estiver vazio, mostra um alerta
        if (!termo) {
            alert("Digite um termo para pesquisar.");
            return;
        }

        // Oculta os campos de descrição, pesquisa e opções após o botao pesquisar ser acionado
        document.getElementById("descricao").style.display = "none";
        document.getElementById("pesquisa").style.display = "none";
        document.getElementById("opcoes").style.display = "none";

        // Envia a pesquisa para o servidor
        fetch("/pesquisar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ entrada: termo, criterio: parseInt(tipo) })
        })
        .then(response => {
            // Se a resposta não for OK, lança um erro
            if (!response.ok) {
                throw new Error("Erro na resposta da rede");
            }
            return response.json();
        })
        .then(data => {
            // Mostra a mensagem de resultado
            const resultadoDiv = document.getElementById("resultado");
            resultadoDiv.innerHTML = `<p>${data.mensagem}</p>`;

            // Se houver recomendações, cria uma lista
            if (data.recomendacoes.length > 0) {
                const lista = document.createElement("ul");
                data.recomendacoes.forEach(livro => {
                    // Formata a avaliação com 2 casas decimais
                    const avaliacao = parseFloat(livro.Avaliação).toFixed(2);
                    // Pega apenas o primeiro autor
                    const primeiroAutor = livro.Autor.split(',')[0];
                    // Oculta caracteres no título se tiver mais de 40 caracteres
                    const tituloTruncado = livro.Título.length > 40 ? livro.Título.substring(0, 40) + '...' : livro.Título;
                    // Cria um item de lista para cada livro
                    const item = document.createElement("li");
                    item.innerHTML = `
                        <div class="livro-info">
                            <span class="livro-titulo">${tituloTruncado}</span>
                            <span class="livro-detalhes">${primeiroAutor} (${livro.Categoria})</span>
                        </div>
                        <div class="livro-avaliacao">⭐ ${avaliacao}</div>
                    `;
                    lista.appendChild(item);
                });
                resultadoDiv.appendChild(lista);
            } else {
                // Se não houver recomendações, mostra uma mensagem
                resultadoDiv.innerHTML += "<p>Nenhum livro encontrado.</p>";
            }

            // Mostra o resultado e muda o texto do botão pesquisar para "Voltar" quando estiver na tela de recomendações
            resultadoDiv.style.display = "block";
            this.textContent = "Voltar";
            this.style.display = "block";
        })
        .catch(error => {
            // Mostra um erro se a pesquisa der erro
            console.error("Erro na pesquisa:", error);
            alert("Ocorreu um erro ao realizar a pesquisa. Tente novamente mais tarde.");
        });
    });
});
