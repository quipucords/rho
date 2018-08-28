Frequently Asked Questions (FAQ)
================================

Below you can find some answers to frequently asked questions:

* Where can I find the logs associated with rho?

  You can find logs associated with rho in the $XDG_DATA_HOME/rho or the
  default, ~/.local/share/rho.

* Where can I find configuration information associated with rho?

  You can find configuration information associated with rho in the
  $XDG_CONFIG_HOME/rho or the default, ~/.config/rho.

* Why is rho not returning the path of JBoss EAP?

  If Java is not installed on the remote system the two tasks for detecting EAP
  will not complete successfully and will not display EAP installation if they
  are present.

* What delimiter does rho use for the CSV report files?

  Rho generates its report in a comma seperated format using ',' as the
  delimiter. Most office software can import this, but you must indicate
  that the delimiter is a comma, as some ".csv" files use tabs or semicolons.

  Importing the file with the incorrect delimiter or a mix of delimiters can
  cause the report to be displayed incorrectly, with the wrong data mapped to the
  headings.

* I can't open my report with my office software! (libreoffice, sheets, excel, etc.)

  Note that the file ending of the report file is determined by the user. If
  you are experiencing this problem, be sure that the report filename has
  :code:`.csv` at the end to help your office software detect its format.
