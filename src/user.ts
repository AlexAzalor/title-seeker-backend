import {Modal} from 'flowbite';
import type {ModalOptions, ModalInterface} from 'flowbite';

// /*
//  * $editUserModal: required
//  * options: optional
//  */

// // For your js code

interface IUser {
  id: number;
  fullname: string;
  first_name: string;
  last_name: string;
  email: string;
  is_deleted: boolean;
}

const $modalElement: HTMLElement = document.querySelector('#editUserModal');
const $addUserModalElement: HTMLElement =
  document.querySelector('#add-user-modal');

const modalOptions: ModalOptions = {
  placement: 'bottom-right',
  backdrop: 'dynamic',
  backdropClasses:
    'bg-gray-900 bg-opacity-50 dark:bg-opacity-80 fixed inset-0 z-40',
  closable: true,
};

const modal: ModalInterface = new Modal($modalElement, modalOptions);
const addModal: ModalInterface = new Modal($addUserModalElement, modalOptions);

const $buttonElements = document.querySelectorAll('.user-edit-button');
$buttonElements.forEach(e =>
  e.addEventListener('click', () => {
    editUser(JSON.parse(e.getAttribute('data-target')));
  }),
);

// closing add user modal
const addModalCloseBtn = document.querySelector('#modalAddCloseButton');
if (addModalCloseBtn) {
  addModalCloseBtn.addEventListener('click', () => {
    addModal.hide();
  });
}

// closing edit modal
const editModalCloseBtn = document.querySelector('#editUserModalCloseButton');
if (editModalCloseBtn) {
  editModalCloseBtn.addEventListener('click', () => {
    modal.hide();
  });
}

// search flow
const searchInput: HTMLInputElement = document.querySelector(
  '#table-search-users',
);
const searchInputButton = document.querySelector('#table-search-user-button');
if (searchInputButton && searchInput) {
  searchInputButton.addEventListener('click', () => {
    const url = new URL(window.location.href);
    url.searchParams.set('q', searchInput.value);
    window.location.href = `${url.href}`;
  });
}
const deleteButtons = document.querySelectorAll('.delete-user-btn');

deleteButtons.forEach(e => {
  e.addEventListener('click', async () => {
    if (confirm('Are sure?')) {
      let id = e.getAttribute('data-user-id');
      const response = await fetch(`/user/delete/${id}`, {
        method: 'DELETE',
      });
      if (response.status == 200) {
        location.reload();
      }
    }
  });
});

function editUser(user: IUser) {
  console.log(user);
  let input: HTMLInputElement = document.querySelector('#user-edit-fullname');
  input.value = user.fullname;
  input = document.querySelector('#user-edit-first-name');
  input.value = user.first_name;
  input = document.querySelector('#user-edit-last-name');
  input.value = user.last_name;
  input = document.querySelector('#user-edit-id');
  input.value = user.id.toString();

  input = document.querySelector('#user-edit-email');
  input.value = user.email;
  input = document.querySelector('#user-edit-password');
  input.value = '*******';
  input = document.querySelector('#user-edit-password_confirmation');
  input.value = '*******';
  input = document.querySelector('#user-edit-next_url');
  input.value = window.location.href;
  modal.show();
}
