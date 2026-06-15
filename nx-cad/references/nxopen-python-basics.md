

Use NXOpen Python journals to automate Siemens NX.


Always start with:

    import NXOpen

    def main():
        session = NXOpen.Session.GetSession()
        work_part = session.Parts.Work
        display_part = session.Parts.Display



    if __name__ == "__main__":
        main()



- NXOpen is not a pip package.
- Do not run NXOpen journals with normal system Python.
- Run journals inside Siemens NX or with the NX journal runner.
- Use `NXOpen.Session.GetSession()` to access the NX session.
- Use `session.Parts.Work` as the active work part.
- Use millimeter templates for new metric parts.
- Save the part after creating geometry.
- Destroy builders after committing them when the API requires it.



Use absolute paths when possible.

On Windows, prefer raw strings:

    output_path = r"C:\temp\nx-models\block.prt"

Do not use unescaped Windows paths like:

    output_path = "C:\temp\nx-models\block.prt"
