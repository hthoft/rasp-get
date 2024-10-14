console.log("loaded");
function getDepartmentsFromDevice() {
  // First, get the system information from the local server
  $.ajax({
    url: "http://127.0.0.1:5000/api/get_departments", // Flask route to get department data
    type: "GET",
    success: function (updateRes) {
      try {
        // Parse the returned department data
        const updateData = updateRes;
        console.log(updateData);

        // Store the department views in an array
        var departments = [
          updateData.department_view_1,
          updateData.department_view_2,
          updateData.department_view_3,
        ];

        // Iterate over the departments and call generateDepartmentSection for each
        departments.forEach(function (deptID) {
          if (deptID) {
            // Check if deptID is not null or undefined
            console.log("Department ID:", deptID);
            generateDepartmentSection(deptID, true); // Assuming generateDepartmentSection is defined elsewhere
          }
        });
      } catch (e) {
        console.error("Error parsing department data: ", e);
      }
    },
    error: function (xhr, status, error) {
      console.error(
        "An AJAX error occurred during the department data call:",
        error
      );
    },
  });
}

document.addEventListener("DOMContentLoaded", function () {
  const updateTimer = document.getElementById("updateTimer");
  let countdown = 30;

  function updateCountdown() {
    if (countdown > 0) {
      updateTimer.textContent = `Opdaterer om ${countdown} sekunder`;
      countdown--;
    } else {
      // When countdown reaches 0, call the refresh function and reset the countdown
      refresh();
      countdown = 30; // Reset countdown after it reaches 0
      updateTimer.textContent = `Opdaterer om ${countdown} sekunder`; // Update the text immediately after reset
    }
  }

  getDepartmentsFromDevice();

  function refresh() {
    // If deviceSN is present, fetch department views from the device
    getDepartmentsFromDevice();
  }
  setInterval(updateCountdown, 1000);
});

function generateDepartmentSection(departmentID, generation) {
  // Use the department ID to form a unique ID for the container
  const containerID = `departmentContainer${departmentID}`;
  let container = document.getElementById(containerID);

  // Check if the container already exists
  if (!container) {
    // Create the container div if it does not exist
    container = document.createElement("div");
    container.className = "container mb-5";
    container.id = containerID; // Set the unique ID

    // Create the row div
    let row = document.createElement("div");
    row.className = "row justify-content-center";

    // Create the column div
    let col = document.createElement("div");
    col.className = "col-md-12";
    col.style = "min-width: 95vw; margin-top: 20px;";

    // Add the headers and table
    col.innerHTML = `
      <h1 class="text-white text-center" id="departmentTitle${departmentID}"></h1>
      <table id="jobsTable${departmentID}" class="center-table border-bottom border-3 border-light shadow-lg" style="min-width:93vw;">
        <thead id="jobsTableHead${departmentID}">
          <!-- Headers will be added dynamically here -->
        </thead>
        <tbody id="jobsTableBody${departmentID}">
          <!-- Rows will be added dynamically here -->
        </tbody>
      </table>`;

    // Append the column to the row, and the row to the container
    row.appendChild(col);
    container.appendChild(row);

    // Find the 'visualizations' div and append the container to it
    const visualizationsDiv = document.getElementById("visualizations");
    if (visualizationsDiv) {
      visualizationsDiv.appendChild(container);
    } else {
      console.error('Div with id "visualizations" not found.');
    }
  }

  // Call the function to populate the data whether it's a new or existing container
  if (generation) {
    getJobsAndTasks(null, null, departmentID);
  }
}

function getCancellationIcon(cancelReason) {
  let iconClass;
  switch (cancelReason) {
    case "material":
      iconClass = "mdi mdi-wrench"; // Example icon for material
      break;
    case "personnel":
      iconClass = "mdi mdi-account-off"; // Example icon for personnel
      break;
    case "equipment":
      iconClass = "mdi mdi-alert-circle-outline"; // Example icon for equipment
      break;
    case "breakdown":
      iconClass = "mdi mdi-stop-circle-outline"; // Example icon for breakdown
      break;
    default:
      iconClass = "mdi mdi-alert"; // Default icon (triangle exclamation)
      break;
  }
  const icon = document.createElement("i");
  icon.className = iconClass;
  return icon;
}

function getJobsAndTasks(projectID, stageID, departmentID) {
  $.ajax({
    url: "http://127.0.0.1:5000/api/get_job_tasks", // Flask route to get department data
    type: "GET",
    data: {
      department_id: departmentID,
    },
    success: function (data) {
      const jobs = data;
      const tableBody = document.getElementById(`jobsTableBody${departmentID}`);
      const tableHead = document.getElementById(`jobsTableHead${departmentID}`);
      const departmentTitle = document.getElementById(
        `departmentTitle${departmentID}`
      );
      tableBody.innerHTML = ""; // Clear existing table rows
      tableHead.innerHTML = "";
      console.log(jobs);
      // After calculating the sum of active users
      let sum = 0;
      let activeUsers = []; // Array to store all active user names

      for (const obj of jobs) {
        for (const task of obj.job_tasks) {
          sum += parseInt(task.active_users_count);

          // Assuming 'active_user_names' is an array of user names in the task object
          if (task.active_user_names && task.active_user_names.length > 0) {
            activeUsers = activeUsers.concat(task.active_user_names); // Collect all active user names
          }
        }
      }

      console.log(`Total active users count: ${sum}`);
      console.log("Active users:", activeUsers); // Log all active user names

      // Check if there are any jobs and set the department title
      if (jobs.length > 0 && jobs[0].department_title) {
        const departmentTitleIcon = document.createElement("i");
        departmentTitleIcon.className = "mdi mdi-account"; // Use the MDI group icon
        departmentTitleIcon.className =
          sum > 0
            ? "mdi mdi-account text-success"
            : "mdi mdi-account-off text-danger";

        const departmentUserCount = document.createElement("span");
        departmentUserCount.textContent = sum + " - ";

        // Apply text-success or text-danger based on the sum
        departmentUserCount.className =
          sum > 0 ? "text-success" : "text-danger";

        departmentTitle.textContent = ""; // Clear the current content
        departmentTitle.appendChild(departmentTitleIcon);
        departmentTitle.appendChild(departmentUserCount);
        departmentTitle.append(` ${jobs[0].department_title}`);
      } else {
        // Handle the case where no jobs are returned or the department title is not set
        departmentTitle.textContent = "No department title available";
      }

      // Filter jobs based on stage_order and stage_status criteria
      const filteredJobs = jobs.filter((job) => {
        if (job.stage_order == 1) {
          return true; // Always show jobs where stage_order is 1
        } else if (job.stage_order > 1) {
          return job.stage_status !== "inactive"; // For stage_order > 1, show if status is not 'inactive'
        }
        return false; // Default case to not show the job
      });

      // Apply the existing logic to the filtered jobs
      const activeJobs = filteredJobs.filter(
        (job) => job.job_status !== "inactive"
      );
      const completedJobs = activeJobs
        .filter(
          (job) =>
            job.job_tasks.length > 0 &&
            job.job_tasks.every((task) => task.job_task_status === "completed")
        )
        .sort((a, b) => {
          const lastTaskA = a.job_tasks.reduce(
            (latest, task) =>
              new Date(task.job_task_end) > new Date(latest.job_task_end)
                ? task
                : latest,
            a.job_tasks[0]
          );
          const lastTaskB = b.job_tasks.reduce(
            (latest, task) =>
              new Date(task.job_task_end) > new Date(latest.job_task_end)
                ? task
                : latest,
            b.job_tasks[0]
          );
          return (
            new Date(lastTaskB.job_task_end) - new Date(lastTaskA.job_task_end)
          );
        })
        .slice(0, 2)
        .reverse(); // Keep only the two newest completed jobs and reverse their order

      const remainingJobs = activeJobs
        .filter(
          (job) =>
            !job.job_tasks.every((task) => task.job_task_status === "completed")
        )
        .sort((a, b) => {
          // If stage_order is 1 for both, sort by job_activation
          if (a.stage_order == 1 && b.stage_order == 1) {
            return new Date(a.job_activation) - new Date(b.job_activation);
          }
          // If stage_order is 1 for 'a' only, 'a' should come first
          if (a.stage_order == 1) {
            return -1;
          }
          // If stage_order is 1 for 'b' only, 'b' should come first
          if (b.stage_order == 1) {
            return 1;
          }
          // If stage_order is greater than 1 for both, sort by stage_activation
          return new Date(a.stage_activation) - new Date(b.stage_activation);
        });

      const sortedJobs = completedJobs.concat(remainingJobs);

      const uniqueProjects = new Set(
        sortedJobs.map((job) => job.project_title)
      );

      if (uniqueProjects.size === 1) {
        // Single unique project, get its title and ID
        const uniqueProjectTitle = uniqueProjects.values().next().value;
        const project = sortedJobs.find(
          (job) => job.project_title === uniqueProjectTitle
        );

        if (project && project.project_id) {
          const jobsTableHead = document.getElementById(
            `jobsTableHead${departmentID}`
          );
          const titleRow = document.createElement("tr");
          const titleHeader = document.createElement("th");

          // This will make the header span all columns
          titleHeader.setAttribute("colspan", "100%");
          titleHeader.classList.add("text-center", "fw-bold", "fs-6", "s-bg"); // Add some classes for styling

          // Create the span for the project title
          const projectSpan = document.createElement("span");
          projectSpan.classList.add(
            "project-badge",
            "rounded-5",
            "px-4",
            "py-1",
            "shadow"
          ); // Class to style the badge
          projectSpan.style.backgroundColor = project.project_color; // Set the background color
          projectSpan.textContent = `${
            project.project_case_id ? `${project.project_case_id} - ` : ""
          }${uniqueProjectTitle} `;

          // Append the projectSpan to the titleHeader
          titleHeader.appendChild(projectSpan);

          // Append the titleHeader to the titleRow, and then titleRow to jobsTableHead
          titleRow.appendChild(titleHeader);
          jobsTableHead.appendChild(titleRow);
        }
      } else {
        // Multiple unique projects, display each with a color in a single row
        const jobsTableHead = document.getElementById(
          `jobsTableHead${departmentID}`
        );
        const titleRow = document.createElement("tr");
        const titleHeader = document.createElement("th");

        // This will make the header span all columns
        titleHeader.setAttribute("colspan", "100%");
        titleHeader.classList.add("text-center", "fw-bold", "fs-6", "s-bg"); // Add some classes for styling

        uniqueProjects.forEach((projectTitle) => {
          const project = sortedJobs.find(
            (job) => job.project_title === projectTitle
          );

          // Create the span for the project title
          const projectSpan = document.createElement("span");
          projectSpan.classList.add(
            "project-badge",
            "rounded-5",
            "px-4",
            "py-1",
            "shadow"
          ); // Class to style the badge
          projectSpan.style.backgroundColor = project.project_color; // Set the background color
          projectSpan.textContent = `${
            project.project_case_id ? `${project.project_case_id} - ` : ""
          }${projectTitle} `;

          // Append the projectSpan to the titleHeader
          titleHeader.appendChild(projectSpan);

          // Add spacing or a separator between project badges if desired
          const separator = document.createElement("span");
          separator.innerHTML = "&nbsp;"; // Non-breaking space as a separator
          titleHeader.appendChild(separator);
        });

        // Append the titleHeader to the titleRow, and then titleRow to jobsTableHead
        titleRow.appendChild(titleHeader);
        jobsTableHead.appendChild(titleRow);
      }
      const activeUsersRow = document.createElement("tr");
      const activeUsersCell = document.createElement("td");
      activeUsersCell.setAttribute("colspan", "100%"); // Span all columns
      activeUsersCell.classList.add(
        "text-center",
        "fw-bold",
        "fs-6",
        "p-2",
        "s-bg",
        "py-1"
      ); // Add some classes for styling
      activeUsersCell.style.height = "40px"; // Set height to auto to allow wrapping

      // Check if there are active users
      if (activeUsers.length) {
        // Loop through each active user and create a badge for them
        activeUsers.forEach((user) => {
          const userBadge = document.createElement("span");
          userBadge.classList.add(
            "badge",
            "bg-dark",
            "mx-1",
            "px-2",
            "py-1",
            "fs-4"
          ); // Add badge classes for styling
          userBadge.textContent = user; // Set the user's name as the badge content
          activeUsersCell.appendChild(userBadge); // Append the badge to the cell
        });
      } else {
        // If no active users, display 'No active users'
        activeUsersCell.textContent = "No active users";
      }

      // Append the active users row to the table head
      activeUsersRow.appendChild(activeUsersCell);
      tableHead.appendChild(activeUsersRow);

      let taskCounts = {};
      sortedJobs.forEach((job) => {
        job.job_tasks.forEach((task) => {
          taskCounts[task.job_task_name] = Math.max(
            taskCounts[task.job_task_name] || 0,
            job.job_tasks.filter((t) => t.job_task_name === task.job_task_name)
              .length
          );
        });
      });

      // Determine the number of remaining columns
      let totalTaskCount = Object.values(taskCounts).reduce(
        (acc, count) => acc + count,
        0
      );

      // Set the width for the first column
      let firstColumnWidth = 200; // in pixels

      // Calculate the width for the remaining columns as a percentage
      let remainingWidthPercentage =
        100 - (firstColumnWidth / tableHead.offsetWidth) * 100;
      let eachColumnWidthPercentage = remainingWidthPercentage / totalTaskCount;

      // Construct the table header
      tableHead.innerHTML +=
        '<tr><th class="s-bg text-center" style="width:200px;">Job</th>' +
        Object.entries(taskCounts)
          .map(([name, count]) =>
            Array(count)
              .fill(
                `<th class="s-bg text-center fw-bolder fs-6" style="width:${eachColumnWidthPercentage}%;">${name}</th>`
              )
              .join("")
          )
          .join("") +
        "</tr>";

      sortedJobs.forEach((job) => {
        if (job.job_tasks.length === 0) {
          return;
        }
        const row = document.createElement("tr");

        const allTasksCompleted = job.job_tasks.every(
          (task) => task.job_task_status === "completed"
        );
        const statusClass = allTasksCompleted ? "c-bg" : "s-bg";

        if (statusClass) {
          row.classList.add(statusClass);
        }

        const jobTitleCell = document.createElement("td");
        jobTitleCell.style.textAlign = "left";
        jobTitleCell.classList.add(
          "fw-bolder",
          statusClass,
          "ps-4",
          "fs-5",
          "border-end",
          "border-3",
          "border-light",
          "shadow-lg"
        );

        // Add color indicator if there are multiple unique projects and color is available
        if (!projectID) {
          const uniqueProjects = new Set(
            sortedJobs.map((job) => job.project_title)
          );
          if (uniqueProjects.size >= 1 && job.project_color) {
            const colorIndicator = document.createElement("span");
            colorIndicator.classList.add(
              "mdi",
              "mdi-circle",
              "me-2",
              "text-left"
            );
            colorIndicator.style.cssText = `-webkit-text-fill-color: ${job.project_color} !important;`;
            jobTitleCell.prepend(colorIndicator); // Add the color indicator before the job title
          }
        }

        const jobTitleText = document.createTextNode(job.job_title);
        jobTitleCell.appendChild(jobTitleText);

        row.appendChild(jobTitleCell);

        Object.keys(taskCounts).forEach((taskName) => {
          let tasks = job.job_tasks.filter(
            (task) => task.job_task_name === taskName
          );
          for (let i = 0; i < taskCounts[taskName]; i++) {
            const taskCell = document.createElement("td");
            taskCell.className = "task-cell";

            if (tasks[i]) {
              taskCell.setAttribute("data-job-task-id", tasks[i].job_task_id);

              const taskStatusClass =
                tasks[i].job_task_status === "inactive"
                  ? "n-bg"
                  : tasks[i].job_task_status === "waiting"
                  ? tasks[i].job_task_cancel_reason
                    ? "u-bg-pulse"
                    : "u-bg"
                  : tasks[i].job_task_status === "active"
                  ? tasks[i].job_task_cancel_reason
                    ? "u-bg-pulse"
                    : "u-bg"
                  : tasks[i].job_task_status === "cancelled"
                  ? "w-bg"
                  : tasks[i].job_task_status === "special"
                  ? "c-bg-pulse"
                  : tasks[i].job_task_status === "completed"
                  ? "c-bg"
                  : "";

              if (taskStatusClass) {
                taskCell.classList.add(taskStatusClass);
              }

              taskCell.style.cursor = "pointer"; // Make it visually apparent that the cell is clickable
              taskCell.addEventListener("click", function () {
                window.location.href = `../Registrant/job.php?jobID=${tasks[i].job_id}`;
              });

              // Outermost container
              const containerDiv = document.createElement("div");
              containerDiv.className =
                "d-flex flex-column justify-content-center align-items-center";

              // Inner container for the label and the count, and later the countdown span
              const labelCountContainer = document.createElement("div");
              labelCountContainer.className =
                "d-flex flex-column justify-content-center";

              // Container for the label and the count
              const labelCountDiv = document.createElement("div");
              labelCountDiv.className = "fw-bolder d-flex";

              // Label part
              if (tasks[i].job_task_label) {
                const labelDiv = document.createElement("div");
                labelDiv.textContent = `${tasks[i].job_task_label} `;
                labelCountDiv.appendChild(labelDiv);
              }

              // Handle cancellation reason
              if (
                (tasks[i].job_task_status === "cancelled" ||
                  (tasks[i].job_task_status === "active" &&
                    tasks[i].job_task_cancel_reason) ||
                  (tasks[i].job_task_status === "waiting" &&
                    tasks[i].job_task_cancel_reason)) &&
                tasks[i].job_task_cancel_reason
              ) {
                const cancelIcon = getCancellationIcon(
                  tasks[i].job_task_cancel_reason
                );
                cancelIcon.classList.add("ms-1");
                labelCountDiv.appendChild(cancelIcon); // Append the icon to your div or any other element
              }

              if (tasks[i].job_task_status === "special") {
                const specialIcon = document.createElement("i");
                specialIcon.className = "mdi mdi-check-decagram";
                specialIcon.classList.add("ms-1");
                labelCountDiv.appendChild(specialIcon); // Append the icon to your div or any other element
              }

              // Count part
              if (tasks[i].active_users_count > 0) {
                const countDiv = document.createElement("div");
                // Add 'ms-2' only if there is a label
                countDiv.className = `d-flex align-items-center ${
                  tasks[i].job_task_label ? "ms-1" : ""
                }`;
                const icon = document.createElement("i");
                icon.className = "bi bi-person-fill";
                countDiv.appendChild(icon);
                const countText = document.createTextNode(
                  ` ${tasks[i].active_users_count}`
                );
                countDiv.appendChild(countText);
                labelCountDiv.appendChild(countDiv);
              }

              labelCountContainer.appendChild(labelCountDiv); // Add the label and count div to the inner container

              // The countdown span will be added dynamically in updateTaskCompletion function
              // Make sure to append it to labelCountContainer, not containerDiv
              taskCell.style.border = "1px solid black";

              containerDiv.appendChild(labelCountContainer); // Add the inner container to the outer container
              taskCell.appendChild(containerDiv); // Add the outer container to the task cell

              if (
                (tasks[i].job_task_status === "active" ||
                  tasks[i].job_task_status === "waiting" ||
                  tasks[i].job_task_status === "inactive" ||
                  tasks[i].job_task_status === "cancelled") &&
                !isNaN(parseFloat(tasks[i].job_task_progress))
              ) {
                const progressBar = document.createElement("div");

                // Add Bootstrap classes for striped progress bar
                progressBar.className =
                  "shadow progress-bar progress-bar-striped";

                // Use Bootstrap's progress-bar-animated class if the task is active or waiting
                if (
                  tasks[i].job_task_status === "active" ||
                  tasks[i].job_task_status === "waiting" ||
                  tasks[i].job_task_status === "inactive"
                ) {
                  progressBar.classList.add("progress-bar-animated");
                }

                progressBar.style.width = `${parseFloat(
                  tasks[i].job_task_progress
                )}%`;
                progressBar.style.height = "100%";

                if (tasks[i].job_task_status === "inactive") {
                  progressBar.style.backgroundImage =
                    "linear-gradient(45deg, rgba(255, 255, 0, 0.6) 25%, transparent 25%, transparent 50%, rgba(255, 255, 0, 0.6) 50%, rgba(255, 255, 0, 0.6) 75%, transparent 75%, transparent)";
                }

                // Append progressBar after containerDiv so it doesn't overlay the text
                taskCell.appendChild(progressBar);
              }

              if (tasks[i].job_task_est_completion) {
                updateTaskCompletion(
                  taskCell,
                  tasks[i].job_task_label,
                  tasks[i].job_task_est_completion,
                  tasks[i].job_task_status === "completed"
                );
              }
            } else {
              taskCell.classList.add("g-bg");
              taskCell.textContent = "";
            }

            row.appendChild(taskCell);
          }
        });

        tableBody.appendChild(row);
      });
    },
    error: function (err) {
      console.error(err);
    },
  });
}

function updateTaskCompletion(
  taskCell,
  jobTaskLabel,
  estCompletion,
  isCompleted
) {
  if (isCompleted) {
    // If the task is completed, just show the label and return
    taskCell.innerHTML = jobTaskLabel ? `${jobTaskLabel} ` : "";
    return;
  }

  const getFormattedCountdown = (estDate) => {
    const now = new Date();
    let delta = Math.abs(estDate - now) / 1000;

    // Calculate difference in hours and minutes
    const hours = Math.floor(delta / 3600) % 24;
    delta -= hours * 3600;
    const minutes = Math.floor(delta / 60) % 60;

    return `${hours}t ${minutes}m`;
  };

  // Find or create the containerDiv
  let labelCountContainer = taskCell.querySelector(".label-count-container");
  if (!labelCountContainer) {
    labelCountContainer = document.createElement("div");
    labelCountContainer.className =
      "label-count-container d-flex flex-column justify-content-center align-items-center";
    taskCell.appendChild(labelCountContainer);
  }

  // Determine the countdown
  const estDate = new Date(estCompletion);
  const countdown = getFormattedCountdown(estDate);

  const options = { hour: "2-digit", minute: "2-digit" };
  const timeFormat = estDate.toLocaleTimeString([], options);

  // Create and append the countdown span
  const countdownSpan = document.createElement("span");
  countdownSpan.className = "fs-2";
  countdownSpan.textContent =
    new Date() > estDate ? `+${timeFormat}` : timeFormat;

  // Use inline style to set the text color
  if (new Date() > estDate) {
    countdownSpan.style.webkitTextFillColor = "red";

    countdownSpan.classList.add("fw-bolder"); // Set text color to red if the date is past
  } else {
    countdownSpan.classList.add("text-white"); // Use Bootstrap's text-white class if the date is not past
  }

  labelCountContainer.appendChild(countdownSpan);
}
