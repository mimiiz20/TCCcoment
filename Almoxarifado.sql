CREATE DATABASE almoxarifado; /*cria o banco*/

USE almoxarifado;/*ativa o banco*/

CREATE TABLE estoque (/*cria tabela de estoque*/
    id INT PRIMARY KEY AUTO_INCREMENT,/*inteiro, chave principal/não nulo, id único para cada item, se forma sozinho*/
    responsavel VARCHAR(100), /*varchar=caracteres, pra escrever*/
    nome VARCHAR(255),
    categoria VARCHAR (100),
    qtde INT,
    estoque_min INT,
    preco DECIMAL (10,2),
	descricao VARCHAR (500),
    imagem VARCHAR(255)
);

CREATE TABLE usuarios (/*cria tabela de users*/
    id INT PRIMARY KEY AUTO_INCREMENT,
    user VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    tipo VARCHAR(20) NOT NULL DEFAULT 'usuario', /*default=padrão, obrigatoriamente vai ser um usuario*/
    senha VARCHAR(255) NOT NULL
);

INSERT INTO estoque (responsavel, nome, categoria, qtde, estoque_min, preco, descricao, imagem) /*coloca itens na tabela*/
VALUES ("Róger", "Chave Fenda", "Mecatrônica", 12, 24, 25.00, "Chave de fenda pequena", "/static/chave_fenda.jpg"); /*valores necessarios da tabela*/
INSERT INTO estoque (responsavel, nome, categoria, qtde, estoque_min, preco, descricao, imagem)
VALUES ("Viviane", "Alicate", "Mecatrônica", 8, 28, 28.00, "Alicate da marca Tramontina", "/static/alicate.jpg");

INSERT INTO usuarios (user, email, tipo, senha)
VALUES ('Administrador', 'admin@empresa.com', 'admin', '$2a$12$glWRAuHWTu6VOfiVxBmFNON0HiHey93me9JvMPsTEnNrI0GcB3aMW');
INSERT INTO usuarios (user, email, tipo, senha)
VALUES ('João', 'joao@empresa.com', 'usuário', '$2a$12$Oc1gJWh92oGDc/EO9oKyu.UjP/gCljBFZPZpRln1tqvu8LubErSEW');	

SELECT * FROM estoque; /*seleciona tudo que está na tabela para ser mostrado*/
SELECT * FROM usuarios;

DROP TABLE estoque; /*apagar a tabela (ela deixa de existir)*/
DROP TABLE usuarios;

TRUNCATE TABLE estoque; /*não ta funcionando - exclui tudo da tabela (deixa ela vazia)*/
TRUNCATE TABLE usuarios;