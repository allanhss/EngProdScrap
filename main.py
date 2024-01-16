from Obsidian import Obsidian
from SIGAA import SIGAA


if __name__ == "__main__":
    siga = SIGAA()

    obsidian = Obsidian(
        gradeDF=siga.curriculo.df,
        historicoDF=siga.historico,
    )

    ...
